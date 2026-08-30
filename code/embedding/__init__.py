"""Embedding package (model + Phase 3 pipeline).

Submodules are imported lazily so the runtime app (which only needs
embedding.model) never pulls in the ingest pipeline / bs4 / torch.
Use `from embedding.model import ...` directly.
"""

from __future__ import annotations

from embedding.model import EMBEDDING_DIM, MODEL_NAME, embed_texts, get_model

__all__ = ["EMBEDDING_DIM", "MODEL_NAME", "embed_texts", "get_model", "run_phase3"]


def run_phase3(*, source_ids: list[int] | None = None) -> dict:
    from embedding.pipeline import run_phase3 as _run

    return _run(source_ids=source_ids)
