"""GET only an allowlisted URL. No crawl, no login."""

from __future__ import annotations

from dataclasses import dataclass

import requests

from corpus.allowlist import ALLOWED_URLS

USER_AGENT = (
    "Mozilla/5.0 (compatible; NextleapRAGPrototype/0.1; +public-corpus-ingest)"
)
TIMEOUT_SECONDS = 90


class FetchError(Exception):
    def __init__(self, reason: str, http_status: int | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.http_status = http_status


@dataclass(frozen=True)
class FetchResult:
    payload: bytes
    content_type: str
    final_url: str


def fetch_allowlisted(url: str) -> FetchResult:
    if url not in ALLOWED_URLS:
        raise FetchError("refused: URL is not on the closed allowlist")

    try:
        response = requests.get(
            url,
            timeout=TIMEOUT_SECONDS,
            headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
            allow_redirects=True,
        )
    except requests.RequestException as exc:
        raise FetchError(f"request_failed: {exc.__class__.__name__}") from exc

    if response.status_code == 404:
        raise FetchError("http_404", http_status=404)
    if response.status_code >= 400:
        raise FetchError(f"http_{response.status_code}", http_status=response.status_code)

    payload = response.content or b""
    if not payload:
        raise FetchError("empty_body", http_status=response.status_code)

    content_type = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    return FetchResult(
        payload=payload,
        content_type=content_type,
        final_url=url,
    )
