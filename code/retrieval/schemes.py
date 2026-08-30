"""Detect which of the five schemes (if any) a user question names.

Used by retrieval to prefer matching-scheme chunks (E12) and to surface
ambiguity (PRD §6.2) instead of collapsing five schemes into one answer.
"""

from __future__ import annotations

import re
from typing import Literal

Scheme = Literal["large_cap", "flexicap", "elss", "midcap", "small_cap"]

# Substrings that indicate a scheme is named, mapped to the canonical scheme
# key. Order matters: check the most specific terms first.
SCHEME_ALIASES: tuple[tuple[Scheme, tuple[str, ...]], ...] = (
    ("large_cap", ("large cap", "largecap", "blue chip", "bluechip")),
    ("flexicap", ("flexi cap", "flexicap")),
    ("elss", ("elss", "tax saver", "long term equity")),
    ("midcap", ("mid cap", "midcap", "magnum midcap")),
    ("small_cap", ("small cap", "smallcap")),
)


def detect_scheme(question: str) -> Scheme | None:
    """Return the scheme named in the question, or None if none is named.

    Word-boundary matching tolerates surrounding punctuation ("ELSS?",
    "SBI Small Cap Fund.") so the scheme is still detected.
    """
    lowered = question.lower()
    for scheme, aliases in SCHEME_ALIASES:
        for alias in aliases:
            if re.search(rf"\b{re.escape(alias)}\b", lowered):
                return scheme
    return None
