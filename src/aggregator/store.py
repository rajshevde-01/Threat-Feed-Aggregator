import json
import os
import re
import sqlite3
from ipaddress import ip_address, ip_network, AddressValueError
from typing import Iterable


def _ip_in_cidr(ip_str: str, cidr_str: str) -> bool:
    """Check if an IP address is within a CIDR range."""
    try:
        ip = ip_address(ip_str)
        network = ip_network(cidr_str, strict=False)
        return ip in network
    except (AddressValueError, ValueError):
        return False


def _matches_regex(value: str, pattern: str) -> bool:
    """Check if a value matches a regex pattern."""
    try:
        return bool(re.search(pattern, value, re.IGNORECASE))
    except re.error:
        return False


def init_db(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS iocs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(type, value)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ioc_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ioc_id INTEGER NOT NULL,
                source TEXT NOT NULL,
                severity TEXT NOT NULL,
                date_added TEXT NOT NULL,
                UNIQUE(ioc_id, source),
                FOREIGN KEY(ioc_id) REFERENCES iocs(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_iocs_type ON iocs(type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_iocs_value ON iocs(value)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sources_source ON ioc_sources(source)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sources_severity ON ioc_sources(severity)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sources_date ON ioc_sources(date_added)")


def upsert_iocs(path: str, iocs: Iterable[dict]) -> int:
    init_db(path)
    inserted = 0
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        for ioc in iocs:
            cursor.execute(
                "INSERT OR IGNORE INTO iocs (type, value, created_at) VALUES (?, ?, ?)",
                (ioc["type"], ioc["value"], ioc["date_added"]),
            )
            cursor.execute(
                "SELECT id FROM iocs WHERE type = ? AND value = ?",
                (ioc["type"], ioc["value"]),
            )
            row = cursor.fetchone()
            if not row:
                continue
            ioc_id = row[0]
            cursor.execute(
                """
                INSERT OR IGNORE INTO ioc_sources (ioc_id, source, severity, date_added)
                VALUES (?, ?, ?, ?)
                """,
                (ioc_id, ioc["source"], ioc["severity"], ioc["date_added"]),
            )
            if cursor.rowcount:
                inserted += 1
        conn.commit()
    return inserted


def search_iocs(
    path: str,
    query: str = "",
    ioc_type: str = "",
    source: str = "",
    severity: str = "",
    search_mode: str = "simple",
    date_from: str = "",
    date_to: str = "",
    limit: int | None = None,
    offset: int = 0,
) -> list[dict]:
    """Search IOCs with optional advanced filters.
    
    Args:
        path: Database path
        query: Search query string
        ioc_type: Filter by IOC type
        source: Filter by source
        severity: Filter by severity
        search_mode: "simple" (LIKE), "regex", or "cidr"
        date_from: ISO date string (YYYY-MM-DD)
        date_to: ISO date string (YYYY-MM-DD)
        limit: Result limit
        offset: Result offset
    """
    init_db(path)
    sql = (
        "SELECT iocs.type, iocs.value, ioc_sources.source, ioc_sources.severity, ioc_sources.date_added "
        "FROM iocs JOIN ioc_sources ON ioc_sources.ioc_id = iocs.id"
    )
    clauses = []
    params: list[object] = []
    
    if ioc_type:
        clauses.append("LOWER(iocs.type) = ?")
        params.append(ioc_type.lower())
    if source:
        clauses.append("LOWER(ioc_sources.source) = ?")
        params.append(source.lower())
    if severity:
        clauses.append("LOWER(ioc_sources.severity) = ?")
        params.append(severity.lower())
    if date_from:
        clauses.append("DATE(ioc_sources.date_added) >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("DATE(ioc_sources.date_added) <= ?")
        params.append(date_to)
    
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY ioc_sources.date_added DESC"
    
    with sqlite3.connect(path) as conn:
        rows = conn.execute(sql, params).fetchall()
    
    results = [
        {
            "type": row[0],
            "value": row[1],
            "source": row[2],
            "severity": row[3],
            "date_added": row[4],
        }
        for row in rows
    ]
    
    # Apply advanced filtering in-memory (cannot be done in SQL easily)
    if query:
        if search_mode == "regex":
            results = [r for r in results if _matches_regex(r["value"], query)]
        elif search_mode == "cidr":
            results = [r for r in results if r["type"] == "ip" and _ip_in_cidr(r["value"], query)]
        else:  # "simple" (default)
            results = [r for r in results if query.lower() in r["value"].lower()]
    
    # Apply limit and offset after filtering
    if limit is not None:
        results = results[offset : offset + limit]
    elif offset:
        results = results[offset:]
    
    return results


def count_iocs(
    path: str,
    query: str = "",
    ioc_type: str = "",
    source: str = "",
    severity: str = "",
    search_mode: str = "simple",
    date_from: str = "",
    date_to: str = "",
) -> int:
    """Count IOCs with optional advanced filters."""
    # Use search_iocs with no limit to get all matching results
    results = search_iocs(
        path,
        query=query,
        ioc_type=ioc_type,
        source=source,
        severity=severity,
        search_mode=search_mode,
        date_from=date_from,
        date_to=date_to,
    )
    return len(results)


def get_stats(path: str) -> dict:
    init_db(path)
    with sqlite3.connect(path) as conn:
        total_iocs = int(conn.execute("SELECT COUNT(*) FROM iocs").fetchone()[0])
        total_records = int(conn.execute("SELECT COUNT(*) FROM ioc_sources").fetchone()[0])
        total_sources = int(conn.execute("SELECT COUNT(DISTINCT source) FROM ioc_sources").fetchone()[0])
        last_updated = conn.execute("SELECT MAX(date_added) FROM ioc_sources").fetchone()[0]
        by_type = {
            row[0]: int(row[1])
            for row in conn.execute("SELECT type, COUNT(*) FROM iocs GROUP BY type ORDER BY type")
        }
    return {
        "total_iocs": total_iocs,
        "total_records": total_records,
        "total_sources": total_sources,
        "last_updated": last_updated,
        "by_type": by_type,
    }


def get_filter_values(path: str) -> dict:
    init_db(path)
    with sqlite3.connect(path) as conn:
        sources = [row[0] for row in conn.execute("SELECT DISTINCT source FROM ioc_sources ORDER BY source")]
        types = [row[0] for row in conn.execute("SELECT DISTINCT type FROM iocs ORDER BY type")]
        severities = [row[0] for row in conn.execute("SELECT DISTINCT severity FROM ioc_sources ORDER BY severity")]
    return {"sources": sources, "types": types, "severities": severities}


def export_iocs(path: str, output_path: str) -> None:
    iocs = search_iocs(path)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(iocs, handle, indent=2)
