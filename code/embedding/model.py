"""Locked embedding model: sentence-transformers/all-MiniLM-L6-v2.

A single module-level instance is shared by both Phase 3 (ingest) and
Phase 5 (query) so store and query always live in the same vector space.
Never mix models, APIs, or dimensions.
"""

from __future__ import annotations

from typing import Any

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

_model: Any = None
_load_error: Exception | None = None


def get_model() -> Any:
    """Return the shared SentenceTransformer, loading it once."""
    global _model, _load_error  # noqa: PLW0603
    if _model is not None:
        return _model
    if _load_error is not None:
        raise _load_error

    try:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(MODEL_NAME)
    except Exception as exc:  # noqa: BLE001
        _load_error = exc
        raise

    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of chunk texts. Returns one vector per input, same order."""
    model = get_model()
    vectors = model.encode(texts, normalize_embeddings=False)
    return vectors.tolist()
