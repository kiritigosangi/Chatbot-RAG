"""Vector store package (local Chroma + Neon pgvector backends).

Submodules are imported lazily so a Neon-only deployment never pulls in
chromadb/torch. Use `from vector_store.neon_store import ...` directly.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "COLLECTION_NAME",
    "get_collection",
    "rebuild_collection",
    "run_phase4",
    "query_top_k_neon",
]


def _chroma() -> Any:
    from vector_store import store  # deferred: chromadb import

    return store


COLLECTION_NAME = "sbi_mf_chunks"


def get_collection() -> Any:
    return _chroma().get_collection()


def rebuild_collection(**kwargs: Any) -> Any:
    return _chroma().rebuild_collection(**kwargs)


def run_phase4(*, source_ids: list[int] | None = None) -> dict[str, Any]:
    from vector_store import pipeline  # deferred

    return pipeline.run_phase4(source_ids=source_ids)


def query_top_k_neon(query_vector: list[float], *, k: int, scheme: str | None = None) -> list[dict[str, Any]]:
    from vector_store import neon_store  # deferred

    return neon_store.query_top_k(query_vector, k=k, scheme=scheme)
