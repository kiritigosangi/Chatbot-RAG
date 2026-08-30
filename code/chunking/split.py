"""Structure-aware then MiniLM-sized splits. Never merge across sources."""

from __future__ import annotations

import re

# all-MiniLM-L6-v2 max sequence is 256 tokens; stay well under with char budget.
MAX_CHUNK_CHARS = 900
OVERLAP_CHARS = 160
MIN_CHUNK_CHARS = 40

_SID_HEADING = re.compile(
    r"^(?:"
    r"SECTION\s+[IVXLCDM0-9.\- ]{0,24}\S.*"
    r"|PART\s+[IVXLCDAB0-9.\- ]{0,24}\S.*"
    r"|HIGHLIGHTS\s+OF\s+THE\s+SCHEME.*"
    r"|[IVX]{1,7}\.\s+[A-Z][A-Za-z0-9 /&(),.'-]{2,80}"
    r"|#{1,3}\s+\S.+"
    r")$",
    re.IGNORECASE,
)

_FACT_HEADING = re.compile(
    r"^(?:"
    r"exit\s+load|load\s+structure|expense\s+ratio|total\s+expense\s+ratio|\bter\b"
    r"|minimum\s+(?:application|investment|sip|purchase)"
    r"|riskometer|benchmark|lock[- ]?in"
    r"|tax\s+(?:benefits?|treatment|reckoner)"
    r"|scheme\s+(?:type|category|name)"
    r"|investment\s+objective"
    r"|asset\s+allocation"
    r")\s*:?\s*$",
    re.IGNORECASE,
)

_ALL_CAPS_HEADING = re.compile(r"^[A-Z][A-Z0-9 ,/&().'\-]{7,80}$")

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\"'])")


def chunk_text(raw_text: str) -> list[str]:
    """Split one document. Caller must not concatenate different source_ids."""
    cleaned = raw_text.strip()
    if not cleaned:
        return []

    sections = _merge_short_sections(_split_on_headings(cleaned))
    chunks: list[str] = []
    for section in sections:
        chunks.extend(_pack_section(section))
    return [c for c in chunks if len(c) >= MIN_CHUNK_CHARS]


def _merge_short_sections(sections: list[str]) -> list[str]:
    """Keep fact headings (TER, exit load) attached to the following body."""
    merged: list[str] = []
    for section in sections:
        if merged and len(merged[-1]) < MIN_CHUNK_CHARS:
            merged[-1] = f"{merged[-1]}\n{section}"
        else:
            merged.append(section)
    return merged


def _split_on_headings(text: str) -> list[str]:
    lines = text.splitlines()
    split_at: list[int] = [0]
    offset = 0
    for line in lines:
        stripped = line.strip()
        if offset > 0 and _is_heading(stripped):
            split_at.append(offset)
        offset += len(line) + 1

    if len(split_at) < 2:
        return [text]

    sections: list[str] = []
    split_at.append(len(text))
    for start, end in zip(split_at, split_at[1:]):
        piece = text[start:end].strip()
        if piece:
            sections.append(piece)
    return sections or [text]


def _is_heading(line: str) -> bool:
    if not line or len(line) > 100:
        return False
    if _FACT_HEADING.match(line) or _SID_HEADING.match(line):
        return True
    if _ALL_CAPS_HEADING.match(line) and "." not in line.rstrip("."):
        words = line.split()
        return 2 <= len(words) <= 12
    return False


def _pack_section(section: str) -> list[str]:
    if len(section) <= MAX_CHUNK_CHARS:
        return [section]

    sentences = _sentences(section)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        extra = len(sentence) + (1 if current else 0)
        if current and current_len + extra > MAX_CHUNK_CHARS:
            chunks.append(" ".join(current))
            overlap = _overlap_prefix(current)
            current = overlap + [sentence]
            current_len = len(" ".join(current))
            if current_len > MAX_CHUNK_CHARS:
                chunks.extend(_hard_wrap(sentence))
                current = []
                current_len = 0
        else:
            current.append(sentence)
            current_len += extra

    if current:
        chunks.append(" ".join(current))
    return chunks


def _sentences(text: str) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n+", text) if p.strip()]
    out: list[str] = []
    for para in paragraphs:
        parts = _SENTENCE_SPLIT.split(para)
        out.extend(p.strip() for p in parts if p.strip())
    return out or [text.strip()]


def _overlap_prefix(sentences: list[str]) -> list[str]:
    """Keep trailing sentences so TER / exit load / lock-in are not cut mid-fact."""
    kept: list[str] = []
    size = 0
    for sentence in reversed(sentences):
        add = len(sentence) + (1 if kept else 0)
        if size + add > OVERLAP_CHARS:
            break
        kept.append(sentence)
        size += add
    kept.reverse()
    return kept


def _hard_wrap(text: str) -> list[str]:
    """Last resort if a single 'sentence' exceeds the MiniLM budget."""
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + MAX_CHUNK_CHARS, len(text))
        if end < len(text):
            space = text.rfind(" ", start, end)
            if space > start:
                end = space
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        start = end
        while start < len(text) and text[start] == " ":
            start += 1
    return chunks
