"""Core retrieval: embed the question and query the local Chroma collection.

Implements Phase 5 process:
  1. embed question with the same MiniLM used for ingest;
  2. query top-k nearest chunks;
  3. when a scheme is named, prefer that scheme's chunks (post-filter /
     metadata filter) so the answer never mixes schemes (E12);
  4. signal no-coverage / weak similarity rather than invent facts.
"""

from __future__ import annotations

from typing import Any, Literal

from embedding.model import embed_texts
from vector_store.store import get_collection

DEFAULT_K = 5
# Chroma cosine space reports distance = 1 - cosine_similarity to the best
# (closest) retrieved chunk. Coverage is judged by that closest chunk — the one
# that would carry the cited fact — not by the worst chunk in top-k.
WEAK_DISTANCE = 0.55
NO_COVERAGE_DISTANCE = 0.68

Coverage = Literal["covered", "weak", "no_coverage"]


def retrieve(
    question: str,
    *,
    scheme: str | None = None,
    k: int = DEFAULT_K,
) -> dict[str, Any]:
    """Return top-k chunks for a question, preferring `scheme` when given."""
    query_vector = embed_texts([question])[0]
    collection = get_collection()

    # General query first.
    general = _query(collection, query_vector, k=k)
    chunks = general

    # If a scheme is named, re-query restricted to that scheme and prefer it.
    if scheme is not None:
        filtered = _query(collection, query_vector, k=k, where={"scheme": scheme})
        if filtered:
            chunks = filtered

    coverage, max_dist = _coverage(chunks)

    return {
        "question": question,
        "scheme": scheme,
        "coverage": coverage,
        "max_distance": max_dist,
        "chunks": chunks,
        "highlighted_urls": _highlighted_urls(chunks),
    }


def _query(
    collection: Any,
    query_vector: list[float],
    *,
    k: int,
    where: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if k < 1:
        return []
    result = collection.query(
        query_embeddings=[query_vector],
        n_results=k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    chunks: list[dict[str, Any]] = []
    for doc, meta, dist in zip(
        result["documents"][0],
        result["metadatas"][0],
        result["distances"][0],
    ):
        chunks.append(
            {
                "chunk_id": meta["chunk_id"],
                "text": doc,
                "url": meta["url"],
                "source_id": meta["source_id"],
                "scheme": meta["scheme"],
                "doc_type": meta["doc_type"],
                "ingest_at": meta.get("ingest_at") or None,
                "document_date": meta.get("document_date") or None,
                "distance": round(float(dist), 4),
            }
        )
    return chunks


def _coverage(chunks: list[dict[str, Any]]) -> tuple[Coverage, float | None]:
    """Coverage from the closest chunk; the worst chunk does not veto a hit."""
    if not chunks:
        return ("no_coverage", None)
    best = min(c["distance"] for c in chunks)
    if best > NO_COVERAGE_DISTANCE:
        return ("no_coverage", best)
    if best > WEAK_DISTANCE:
        return ("weak", best)
    return ("covered", best)


def _highlighted_urls(chunks: list[dict[str, Any]]) -> list[str]:
    """Distinct urls from retrieved chunks (all must be §9 / allowlisted)."""
    urls: list[str] = []
    for c in chunks:
        if c["url"] not in urls:
            urls.append(c["url"])
    return urls
