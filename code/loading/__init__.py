"""Loading package (Phase 1 ingest).

Imported lazily: the runtime app only needs loading.paths (path constants)
and must not pull in bs4 / requests. Use `from loading.paths import ...`.
"""

from __future__ import annotations

__all__ = ["run_phase1"]


def run_phase1(*, source_ids: list[int] | None = None) -> dict:
    from loading.pipeline import run_phase1 as _run

    return _run(source_ids=source_ids)
