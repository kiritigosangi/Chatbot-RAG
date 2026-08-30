"""Embedding backends for the shared MiniLM-L6-v2 vector space.

Two interchangeable runtimes produce the SAME 384-dim vectors for
sentence-transformers/all-MiniLM-L6-v2:

  - "fastembed" (default): ONNX via fastembed. Lightweight, no torch — used on
    Vercel/serverless to keep cold starts fast.
  - "transformers": torch via sentence-transformers — used for local ingest.

clear_embedding_cache() must be called after a backend switch within a process.
"""

from __future__ import annotations

from typing import Any

from config import embedding_backend

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

_fast_model: Any = None
_tf_model: Any = None
_loaded_backend: str | None = None


def _load_fast() -> Any:
    global _fast_model  # noqa: PLW0603
    if _fast_model is None:
        from fastembed import TextEmbedding

        _fast_model = TextEmbedding(model_name=MODEL_NAME)
    return _fast_model


def _load_tf() -> Any:
    global _tf_model  # noqa: PLW0603
    if _tf_model is None:
        from sentence_transformers import SentenceTransformer

        _tf_model = SentenceTransformer(MODEL_NAME)
    return _tf_model


def get_model() -> Any:
    backend = embedding_backend()
    if backend == "transformers":
        return _load_tf()
    return _load_fast()


def clear_embedding_cache() -> None:
    """Drop cached models; call after changing EMBEDDING_BACKEND in-process."""
    global _fast_model, _tf_model  # noqa: PLW0603
    _fast_model = None
    _tf_model = None


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Returns one vector per input, same order."""
    backend = embedding_backend()
    if backend == "transformers":
        model = _load_tf()
        vectors = model.encode(texts, normalize_embeddings=False)
        return vectors.tolist()

    model = _load_fast()
    vectors = list(model.embed(list(texts)))
    return [v.tolist() for v in vectors]
