from typing import Iterable


def filter_iocs(
    iocs: Iterable[dict],
    query: str = "",
    ioc_type: str = "",
    source: str = "",
    severity: str = "",
) -> list[dict]:
    query_lower = query.lower()
    type_lower = ioc_type.lower()
    source_lower = source.lower()
    severity_lower = severity.lower()

    results = []
    for ioc in iocs:
        value = str(ioc.get("value", ""))
        if query_lower and query_lower not in value.lower():
            continue
        if type_lower and ioc.get("type", "").lower() != type_lower:
            continue
        if source_lower and ioc.get("source", "").lower() != source_lower:
            continue
        if severity_lower and ioc.get("severity", "").lower() != severity_lower:
            continue
        results.append(ioc)
    return results
