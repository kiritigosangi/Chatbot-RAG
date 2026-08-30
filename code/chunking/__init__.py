"""Chunking package (Phase 2 ingest).

Imported lazily so the runtime app never pulls in the ingest pipeline.
Use `from chunking.split import ...` directly when needed.
"""

from __future__ import annotations

__all__ = ["run_phase2"]


def run_phase2(*, source_ids: list[int] | None = None) -> dict:
    from chunking.pipeline import run_phase2 as _run

    return _run(source_ids=source_ids)
