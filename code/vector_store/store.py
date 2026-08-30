"""Local ChromaDB persistence for Phase 4 and Phase 5.

One local Chroma collection only. get_client()/get_collection() are shared
with Phase 5 so retrieval reads the same persisted index. rebuild_collection()
wipes and replaces the persisted store from Phases 1–3 on every ingest re-run.
"""

from __future__ import annotations

from typing import Any

from loading.paths import VECTOR_DB_DIR

COLLECTION_NAME = "sbi_mf_chunks"

_client: Any = None
_collection: Any = None


def get_client() -> Any:
    """Return the shared local Chroma PersistentClient (persist under data/).

    allow_reset enables the full replace of the prototype's single collection
    on each ingest re-run (see rebuild_collection).
    """
    global _client  # noqa: PLW0603
    if _client is None:
        import chromadb
        from chromadb.config import Settings

        VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=str(VECTOR_DB_DIR),
            settings=Settings(allow_reset=True),
        )
    return _client


def get_collection() -> Any:
    """Return the shared query collection (Phase 5 retrieval reads this)."""
    global _collection  # noqa: PLW0603
    if _collection is None:
        _collection = get_client().get_or_create_collection(name=COLLECTION_NAME)
    return _collection


def rebuild_collection(
    *,
    ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict[str, Any]],
) -> Any:
    """Wipe the persisted store and rebuild the single collection from scratch.

    The collection uses cosine HNSW space so Phase 5 retrieval measures the
    MiniLM vectors by cosine similarity (semantically meaningful distances).
    """
    client = get_client()
    client.reset()  # replace, never incremental — no second index
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    cleaned = [_clean_metadata(m) for m in metadatas]
    batch_size = 1000  # Chroma caps a single add batch well below the corpus size
    for start in range(0, len(ids), batch_size):
        end = start + batch_size
        collection.add(
            ids=ids[start:end],
            embeddings=embeddings[start:end],
            documents=documents[start:end],
            metadatas=cleaned[start:end],
        )
    return collection


def _clean_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Chroma metadata only allows str/int/float/bool and forbids None."""
    cleaned: dict[str, Any] = {}
    for key, value in metadata.items():
        if value is None:
            cleaned[key] = ""
        elif isinstance(value, bool):
            cleaned[key] = value
        elif isinstance(value, (str, int, float)):
            cleaned[key] = value
        else:
            cleaned[key] = str(value)
    return cleaned
