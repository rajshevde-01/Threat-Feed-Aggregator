import csv
import io
import json
from typing import Iterable


def parse_txt(text: str) -> Iterable[str]:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        yield stripped


def parse_csv(text: str) -> Iterable[dict]:
    buffer = io.StringIO(text)
    reader = csv.reader(buffer)
    rows = list(reader)
    if not rows:
        return []

    header = [h.strip().lower() for h in rows[0]]
    has_header = any(name in {"value", "ioc", "indicator", "ip", "domain", "url"} for name in header)

    if has_header:
        buffer.seek(0)
        dict_reader = csv.DictReader(buffer)
        return list(dict_reader)

    data = []
    for row in rows:
        if not row:
            continue
        data.append({"value": row[0]})
    return data


def parse_json(text: str) -> Iterable[object]:
    data = json.loads(text)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "items", "iocs"):
            if key in data and isinstance(data[key], list):
                return data[key]
    return []


def parse_feed(text: str, feed_format: str) -> Iterable[object]:
    fmt = feed_format.lower()
    if fmt == "txt":
        return list(parse_txt(text))
    if fmt == "csv":
        return parse_csv(text)
    if fmt == "json":
        return parse_json(text)
    raise ValueError(f"Unsupported format: {feed_format}")
