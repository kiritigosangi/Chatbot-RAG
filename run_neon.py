"""Populate Neon pgvector from the local data/chunks + data/embeddings sidecars.

Run from Chatbot/:  python run_neon.py [--reset] [--source N ...]

Requires DATABASE_URL (Neon) in .env or environment.
  --reset   drop and recreate the chunks table (wipes prior rows).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent / "code"
sys.path.insert(0, str(CODE_DIR))

from config import storage_backend  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Initialize schema and load Phase 2/3 sidecars into Neon.",
    )
    parser.add_argument("--reset", action="store_true", help="Drop and recreate the table.")
    parser.add_argument(
        "--source",
        type=int,
        action="append",
        dest="sources",
        help="Only load this source_id (repeatable). Default: all.",
    )
    args = parser.parse_args(argv)

    if storage_backend() != "neon":
        print("STORAGE != neon; set STORAGE=neon in .env to load into Neon.")
        return 1

    from vector_store import neon_store

    try:
        neon_store.init_schema(drop=args.reset)
        summary = neon_store.load_from_sidecars(source_ids=args.sources)
        print(f"rows: {summary['rows_in_table']}")
        print(f"sources_loaded: {summary['sources_loaded']}")
        print(f"host: {summary['host']}")
        return 0
    except RuntimeError as exc:
        print(f"error: {exc}")
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"error: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
