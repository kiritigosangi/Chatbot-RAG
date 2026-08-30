"""Retrieval orchestration: detect scheme, retrieve top-k, prep for the prompt.

Implements Phase 5's phase-exit contract: a list of k chunks (or empty/weak)
with URLs in the §9 allowlist, ready for the Mistral prompt. Only these
retrieved chunks may enter the prompt (PRD §8). Retrieval never invents facts.
"""

from __future__ import annotations

from typing import Any

from corpus.allowlist import ALLOWED_URLS
from retrieval.retriever import DEFAULT_K, retrieve
from retrieval.schemes import detect_scheme


def retrieve_for_query(
    question: str,
    *,
    k: int = DEFAULT_K,
) -> dict[str, Any]:
    """Detect a named scheme, retrieve top-k, and validate citations (E11)."""
    scheme = detect_scheme(question)
    result = retrieve(question, scheme=scheme, k=k)

    # E11: every cited url must be in the closed §9 allowlist.
    off_list = [
        c["url"] for c in result["chunks"] if c["url"] not in ALLOWED_URLS
    ]
    result["url_not_in_allowlist"] = off_list
    result["ambiguous"] = scheme is None and not _clearly_one_scheme(result)

    result["prompt"] = _build_prompt(result, question=question)
    return result


def _clearly_one_scheme(result: dict[str, Any]) -> bool:
    """True if the top chunks are, with high agreement, a single scheme."""
    schemes: dict[str, int] = {}
    for c in result["chunks"]:
        s = c["scheme"]
        schemes[s] = schemes.get(s, 0) + 1
    if not schemes:
        return False
    top_scheme, top_count = max(schemes.items(), key=lambda kv: kv[1])
    return top_count >= max(1, len(result["chunks"]) // 2)


def _build_prompt(result: dict[str, Any], *, question: str) -> str:
    """Compose the evidence block: only retrieved chunk texts, nothing else."""
    lines = [
        "Question:",
        question,
        "",
        "Retrieved corpus passages (facts only from these):",
    ]
    for i, c in enumerate(result["chunks"], start=1):
        lines.append(f"[{i}] {c['text'].strip()}")
        lines.append(f"    source: {c['url']}")
    lines.append("")
    lines.append("Constraints: facts-only; at most 3 sentences; exactly one citation URL from the retrieved sources; "
                 "refuse investment advice; never invent numbers not present above; if the facts are not in the "
                 "passages, say the fact is not in this corpus.")
    return "\n".join(lines)
