"""Phase 2: chunk Phase 1 ok records. One source_id at a time. Write data/chunks/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from corpus.allowlist import ALLOWED_URLS
from chunking.split import MAX_CHUNK_CHARS, chunk_text
from loading.paths import CHATBOT_ROOT, CHUNKS_DIR, RAW_TEXT_DIR, SOURCE_STEM


def run_phase2(*, source_ids: list[int] | None = None) -> dict[str, Any]:
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    parents = _load_ok_parents(source_ids)
    all_chunks: list[dict[str, Any]] = []
    per_source: list[dict[str, Any]] = []

    for parent in parents:
        chunks = _chunk_parent(parent)
        all_chunks.extend(chunks)
        _write_json(
            CHUNKS_DIR / f"{SOURCE_STEM.format(source_id=parent['source_id'])}.json",
            chunks,
        )
        per_source.append(
            {
                "source_id": parent["source_id"],
                "url": parent["url"],
                "chunk_count": len(chunks),
                "max_chunk_chars": max((len(c["text"]) for c in chunks), default=0),
            }
        )

    jsonl_path = CHUNKS_DIR / "chunks.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for chunk in all_chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    oversize = [c["chunk_id"] for c in all_chunks if len(c["text"]) > MAX_CHUNK_CHARS]
    missing_url = [c["chunk_id"] for c in all_chunks if not c.get("url")]
    off_list = [c["chunk_id"] for c in all_chunks if c["url"] not in ALLOWED_URLS]

    summary = {
        "phase": 2,
        "ok_sources": len(parents),
        "chunk_count": len(all_chunks),
        "max_chunk_chars_budget": MAX_CHUNK_CHARS,
        "oversize_chunk_ids": oversize,
        "missing_url_chunk_ids": missing_url,
        "url_not_in_allowlist_chunk_ids": off_list,
        "sources": per_source,
        "jsonl_path": str(jsonl_path.relative_to(CHATBOT_ROOT)).replace("\\", "/"),
    }
    _write_json(CHUNKS_DIR / "_phase2_summary.json", summary)
    return summary


def _load_ok_parents(source_ids: list[int] | None) -> list[dict[str, Any]]:
    wanted = set(source_ids) if source_ids is not None else None
    parents: list[dict[str, Any]] = []
    for path in sorted(RAW_TEXT_DIR.glob("[0-9][0-9].json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("status") != "ok":
            continue
        source_id = int(record["source_id"])
        if wanted is not None and source_id not in wanted:
            continue
        if not (record.get("raw_text") or "").strip():
            continue
        if record.get("url") not in ALLOWED_URLS:
            continue
        parents.append(record)
    return parents


def _chunk_parent(parent: dict[str, Any]) -> list[dict[str, Any]]:
    source_id = int(parent["source_id"])
    texts = chunk_text(parent["raw_text"])
    chunks: list[dict[str, Any]] = []
    for index, text in enumerate(texts, start=1):
        chunks.append(
            {
                "chunk_id": f"src-{source_id:02d}-chk-{index:04d}",
                "text": text,
                "url": parent["url"],
                "source_id": source_id,
                "scheme": parent["scheme"],
                "doc_type": parent["doc_type"],
                "ingest_at": parent.get("ingest_at"),
                "document_date": parent.get("document_date"),
            }
        )
    return chunks


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
