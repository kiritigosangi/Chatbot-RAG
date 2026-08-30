"""Phase 3: embed Phase 2 chunk text with the locked MiniLM model.

Reads chunk records from data/chunks/, embeds each chunk's text, and writes
inspectable sidecars to data/embeddings/. One vector per chunk_id, in the
model's default order/length. The shared model in embedding.model is reused
by Phase 5 at query time.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from embedding.model import EMBEDDING_DIM, MODEL_NAME, embed_texts
from loading.paths import CHATBOT_ROOT, CHUNKS_DIR, EMBEDDINGS_DIR, SOURCE_STEM


def run_phase3(*, source_ids: list[int] | None = None) -> dict[str, Any]:
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    records = _load_chunk_records(source_ids)
    all_vectors: list[dict[str, Any]] = []
    per_source: list[dict[str, Any]] = []

    for source_id, chunks in records:
        vectors = embed_texts([c["text"] for c in chunks])
        entries = [
            {"chunk_id": chunk["chunk_id"], "vector": vector}
            for chunk, vector in zip(chunks, vectors)
        ]
        _write_json(
            EMBEDDINGS_DIR / f"{SOURCE_STEM.format(source_id=source_id)}.json",
            entries,
        )
        all_vectors.extend(entries)
        per_source.append(
            {
                "source_id": source_id,
                "chunk_count": len(chunks),
                "dim": len(vectors[0]) if vectors else 0,
            }
        )

    jsonl_path = EMBEDDINGS_DIR / "embeddings.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for entry in all_vectors:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    wrong_dim = [
        e["chunk_id"] for e in all_vectors if len(e["vector"]) != EMBEDDING_DIM
    ]

    summary = {
        "phase": 3,
        "model": MODEL_NAME,
        "embedding_dim": EMBEDDING_DIM,
        "embedded_chunk_count": len(all_vectors),
        "wrong_dim_chunk_ids": wrong_dim,
        "sources": per_source,
        "jsonl_path": str(jsonl_path.relative_to(CHATBOT_ROOT)).replace("\\", "/"),
    }
    _write_json(EMBEDDINGS_DIR / "_phase3_summary.json", summary)
    return summary


def _load_chunk_records(source_ids: list[int] | None) -> list[tuple[int, list[dict[str, Any]]]]:
    """Load per-source chunk files from data/chunks/, keyed by source_id."""
    wanted = set(source_ids) if source_ids is not None else None
    records: list[tuple[int, list[dict[str, Any]]]] = []
    for path in sorted(CHUNKS_DIR.glob("[0-9][0-9].json")):
        source_id = int(path.stem)
        if wanted is not None and source_id not in wanted:
            continue
        chunks = json.loads(path.read_text(encoding="utf-8"))
        records.append((source_id, chunks))
    records.sort(key=lambda item: item[0])
    return records


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
