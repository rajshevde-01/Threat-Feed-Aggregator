import datetime as dt
import ipaddress
import re
from typing import Iterable

DOMAIN_RE = re.compile(r"^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$")


def detect_type(value: str) -> str:
    try:
        ipaddress.ip_address(value)
        return "ip"
    except ValueError:
        pass

    try:
        ipaddress.ip_network(value, strict=False)
        return "ip"
    except ValueError:
        pass

    if "://" in value:
        return "url"

    if DOMAIN_RE.match(value):
        return "domain"

    return "unknown"


def normalize_item(item: object, source: str, default_severity: str | None) -> dict | None:
    now = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    if isinstance(item, str):
        value = item.strip()
        if not value:
            return None
        ioc_type = detect_type(value)
        if ioc_type == "unknown":
            return None
        return {
            "type": ioc_type,
            "value": value,
            "source": source,
            "severity": default_severity or "medium",
            "date_added": now,
        }

    if isinstance(item, dict):
        value = (
            item.get("value")
            or item.get("ioc")
            or item.get("indicator")
            or item.get("ip")
            or item.get("domain")
            or item.get("url")
        )
        if not value:
            return None
        value = str(value).strip()
        ioc_type = item.get("type") or detect_type(value)
        if ioc_type == "unknown":
            return None
        return {
            "type": ioc_type,
            "value": value,
            "source": source,
            "severity": item.get("severity") or default_severity or "medium",
            "date_added": item.get("date_added") or now,
        }

    return None


def normalize_items(items: Iterable[object], source: str, default_severity: str | None) -> list[dict]:
    normalized = []
    for item in items:
        ioc = normalize_item(item, source=source, default_severity=default_severity)
        if ioc:
            normalized.append(ioc)
    return normalized
