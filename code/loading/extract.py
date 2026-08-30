"""Visible text from HTML and PDFs. No extra URLs, no screenshots."""

from __future__ import annotations

import re
from io import BytesIO

from bs4 import BeautifulSoup
from pypdf import PdfReader

MIN_TEXT_CHARS = 50

_DATE_PATTERNS = (
    re.compile(
        r"\b(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+20\d{2}\b",
        re.I,
    ),
    re.compile(r"\bFY\s*20\d{2}\s*[–-]\s*20\d{2}\b", re.I),
    re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-\s]+20\d{2}\b", re.I),
)


def is_pdf_bytes(payload: bytes) -> bool:
    return payload[:5] == b"%PDF-"


def extract_html_text(payload: bytes) -> str:
    soup = BeautifulSoup(payload, "html.parser")
    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    return _normalize_whitespace(text)


def extract_pdf_text(payload: bytes) -> str:
    reader = PdfReader(BytesIO(payload))
    pages: list[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return _normalize_whitespace("\n".join(pages))


def extract_text(payload: bytes, *, treat_as_pdf: bool) -> str:
    if treat_as_pdf or is_pdf_bytes(payload):
        return extract_pdf_text(payload)
    return extract_html_text(payload)


def document_date_from_text(text: str, fallback: str | None) -> str | None:
    sample = text[:8000]
    for pattern in _DATE_PATTERNS:
        match = pattern.search(sample)
        if match:
            return match.group(0).strip()
    return fallback


def _normalize_whitespace(text: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    compact = "\n".join(line for line in lines if line)
    return compact.strip()
