"""Environment configuration for the RAG chatbot.

Reads .env from Chatbot/ and exposes the settings the pipeline and UI need.
Never commit real secrets; .env is git-ignored.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None  # type: ignore[assignment]

_CODE_DIR = Path(__file__).resolve().parent
_CHATBOT_ROOT = _CODE_DIR.parent


def _load_env() -> None:
    if load_dotenv is None:
        return
    load_dotenv(_CHATBOT_ROOT / ".env", override=False)


@lru_cache(maxsize=1)
def get_settings() -> dict[str, str]:
    """Return resolved settings, loading .env once per process."""
    _load_env()
    return {
        # "neon" -> use Neon pgvector; anything else ("chroma") -> local Chroma.
        "storage": os.environ.get("STORAGE", "neon"),
        "database_url": os.environ.get(
            "DATABASE_URL",
            os.environ.get("NEON_DATABASE_URL", ""),
        ),
        "embedding_backend": os.environ.get("EMBEDDING_BACKEND", "fastembed"),
        "mistral_api_key": os.environ.get("MISTRAL_API_KEY", ""),
        "mistral_model": os.environ.get("MISTRAL_MODEL", "mistral-small-latest"),
    }


def database_url() -> str | None:
    return get_settings()["database_url"].strip() or None


def storage_backend() -> str:
    return (get_settings()["storage"] or "neon").strip().lower()


def embedding_backend() -> str:
    return (get_settings()["embedding_backend"] or "fastembed").strip().lower()
