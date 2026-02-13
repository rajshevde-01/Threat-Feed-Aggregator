from typing import Mapping

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_HEADERS = {
    "User-Agent": "ThreatFeedAggregator/1.0",
    "Accept": "*/*",
}


def _build_session(retries: int, backoff: float) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_feed(
    url: str,
    headers: Mapping[str, str] | None = None,
    timeout: int = 20,
    retries: int = 3,
    backoff: float = 0.5,
) -> str:
    session = _build_session(retries=retries, backoff=backoff)
    merged_headers = dict(DEFAULT_HEADERS)
    if headers:
        merged_headers.update(headers)
    response = session.get(url, timeout=timeout, headers=merged_headers)
    response.raise_for_status()
    return response.text
