"""Phase 4: build the local Chroma collection from Phases 2–3 sidecars.

For each ok source: join its chunk records (data/chunks/) with its embedding
sidecar (data/embeddings/), then rebuild the single Chroma collection under
data/vector_db/. Skipped IDs never appear because they have no chunks.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loading.paths import (
    CHATBOT_ROOT,
    CHUNKS_DIR,
    EMBEDDINGS_DIR,
    SOURCE_STEM,
    VECTOR_DB_DIR,
)
from vector_store.store import COLLECTION_NAME, get_collection, rebuild_collection


def run_phase4(*, source_ids: list[int] | None = None) -> dict[str, Any]:
    pairs = _load_pairs(source_ids)
    ids: list[str] = []
    embeddings: list[list[float]] = []
    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []

    missing_vector: list[str] = []
    for source_id, chunks in pairs:
        vectors = _vectors_by_chunk_id(source_id)
        for chunk in chunks:
            vector = vectors.get(chunk["chunk_id"])
            if vector is None:
                missing_vector.append(chunk["chunk_id"])
                continue
            ids.append(chunk["chunk_id"])
            embeddings.append(vector)
            documents.append(chunk["text"])
            metadatas.append(_metadata(chunk))

    rebuild_collection(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    queryable = _verify_queryable()

    summary = {
        "phase": 4,
        "collection_name": COLLECTION_NAME,
        "stored_count": get_collection().count(),
        "queryable": queryable,
        "chunks_without_embedding": missing_vector,
        "persist_dir": str(VECTOR_DB_DIR.relative_to(CHATBOT_ROOT)).replace("\\", "/"),
        "stored": pairs,
    }
    _write_json(VECTOR_DB_DIR / "_phase4_summary.json", summary)
    return summary


def _verify_queryable() -> bool:
    """Prove the local Chroma collection is readable (phase-4 exit)."""
    try:
        collection = get_collection()
        collection.peek(limit=1) if collection.count() else None
        return True
    except Exception:  # noqa: BLE001
        return False


def _load_pairs(source_ids: list[int] | None) -> list[tuple[int, list[dict[str, Any]]]]:
    wanted = set(source_ids) if source_ids is not None else None
    pairs: list[tuple[int, list[dict[str, Any]]]] = []
    for path in sorted(CHUNKS_DIR.glob("[0-9][0-9].json")):
        source_id = int(path.stem)
        if wanted is not None and source_id not in wanted:
            continue
        chunks = json.loads(path.read_text(encoding="utf-8"))
        pairs.append((source_id, chunks))
    pairs.sort(key=lambda item: item[0])
    return pairs


def _vectors_by_chunk_id(source_id: int) -> dict[str, list[float]]:
    path = EMBEDDINGS_DIR / f"{SOURCE_STEM.format(source_id=source_id)}.json"
    if not path.exists():
        return {}
    entries = json.loads(path.read_text(encoding="utf-8"))
    return {entry["chunk_id"]: entry["vector"] for entry in entries}


def _metadata(chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "chunk_id": chunk["chunk_id"],
        "url": chunk["url"],
        "source_id": int(chunk["source_id"]),
        "scheme": chunk["scheme"],
        "doc_type": chunk["doc_type"],
        "ingest_at": chunk.get("ingest_at"),
        "document_date": chunk.get("document_date"),
    }


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
