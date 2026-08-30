"""Phase 1: load closed corpus into data/raw and data/skips."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from corpus.allowlist import SOURCES, Source, assert_closed_corpus, get_source
from loading.extract import (
    MIN_TEXT_CHARS,
    document_date_from_text,
    extract_text,
)
from loading.fetch import FetchError, fetch_allowlisted
from loading.paths import (
    CHATBOT_ROOT,
    RAW_HTML_DIR,
    RAW_PDF_DIR,
    RAW_TEXT_DIR,
    SKIPS_DIR,
    SOURCE_STEM,
    ensure_data_dirs,
    upload_candidates,
)


class Skip(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def run_phase1(
    *,
    source_ids: list[int] | None = None,
    uploads_only: bool = False,
) -> dict[str, Any]:
    assert_closed_corpus()
    ensure_data_dirs()
    ingest_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    targets = SOURCES if source_ids is None else [get_source(i) for i in source_ids]
    records: list[dict[str, Any]] = []
    for source in targets:
        records.append(_load_one(source, ingest_at=ingest_at, uploads_only=uploads_only))

    summary = {
        "phase": 1,
        "ingest_at": ingest_at,
        "ok": sum(1 for r in records if r["status"] == "ok"),
        "skipped": sum(1 for r in records if r["status"] == "skipped"),
        "records": records,
    }
    _write_json(RAW_TEXT_DIR / "_phase1_summary.json", summary)
    _write_json(
        SKIPS_DIR / "skips.json",
        [r for r in records if r["status"] == "skipped"],
    )
    return summary


def _load_one(source: Source, *, ingest_at: str, uploads_only: bool) -> dict[str, Any]:
    try:
        payload, origin = _read_payload(source, uploads_only=uploads_only)
        treat_as_pdf = _is_pdf(source["url"], payload)
        raw_text = extract_text(payload, treat_as_pdf=treat_as_pdf)
        if len(raw_text) < MIN_TEXT_CHARS:
            raise Skip("empty_body")
    except Skip as exc:
        return _skipped(source, ingest_at, reason=exc.reason)
    except FetchError as exc:
        return _skipped(source, ingest_at, reason=exc.reason)
    except Exception as exc:  # noqa: BLE001 — skip this ID; never swap URL
        return _skipped(source, ingest_at, reason=f"extract_failed: {exc.__class__.__name__}")

    stem = SOURCE_STEM.format(source_id=source["source_id"])
    binary_dir = RAW_PDF_DIR if treat_as_pdf else RAW_HTML_DIR
    suffix = ".pdf" if treat_as_pdf else ".html"
    binary_path = binary_dir / f"{stem}{suffix}"
    binary_path.write_bytes(payload)

    record = {
        "source_id": source["source_id"],
        "url": source["url"],
        "scheme": source["scheme"],
        "doc_type": source["doc_type"],
        "title": source["title"],
        "raw_text": raw_text,
        "document_date": document_date_from_text(raw_text, source["document_date"]),
        "ingest_at": ingest_at,
        "status": "ok",
        "origin": origin,
        "binary_path": str(binary_path.relative_to(CHATBOT_ROOT)).replace("\\", "/"),
    }
    text_path = RAW_TEXT_DIR / f"{stem}.json"
    _write_json(text_path, record)
    return {k: v for k, v in record.items() if k != "raw_text"} | {
        "raw_text_chars": len(raw_text),
        "text_path": str(text_path.relative_to(CHATBOT_ROOT)).replace("\\", "/"),
    }


def _read_payload(source: Source, *, uploads_only: bool) -> tuple[bytes, str]:
    uploads = upload_candidates(source["source_id"])
    if uploads:
        path = uploads[0]
        payload = path.read_bytes()
        if not payload:
            raise Skip("empty_body")
        return payload, f"upload:{path.name}"

    if uploads_only:
        raise Skip("no_upload")

    result = fetch_allowlisted(source["url"])
    return result.payload, "fetch"


def _is_pdf(url: str, payload: bytes) -> bool:
    from loading.extract import is_pdf_bytes

    if is_pdf_bytes(payload):
        return True
    return url.lower().split("?", 1)[0].endswith(".pdf")


def _skipped(source: Source, ingest_at: str, *, reason: str) -> dict[str, Any]:
    record = {
        "source_id": source["source_id"],
        "url": source["url"],
        "scheme": source["scheme"],
        "doc_type": source["doc_type"],
        "title": source["title"],
        "raw_text": "",
        "document_date": source["document_date"],
        "ingest_at": ingest_at,
        "status": "skipped",
        "skip_reason": reason,
    }
    stem = SOURCE_STEM.format(source_id=source["source_id"])
    _write_json(SKIPS_DIR / f"{stem}.json", record)
    return {k: v for k, v in record.items() if k != "raw_text"}


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
