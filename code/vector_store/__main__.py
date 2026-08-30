from __future__ import annotations

import argparse
import json
import sys

from vector_store.pipeline import run_phase4


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 4 vector store: build local Chroma collection from Phases 2–3 into data/vector_db/.",
    )
    parser.add_argument(
        "--source-id",
        type=int,
        action="append",
        dest="source_ids",
        help="Store only this source_id (repeatable). Default: all chunked sources.",
    )
    args = parser.parse_args(argv)

    if args.source_ids:
        for source_id in args.source_ids:
            if source_id < 1 or source_id > 25:
                print(f"source_id must be 1–25, got {source_id}", file=sys.stderr)
                return 2

    summary = run_phase4(source_ids=args.source_ids)
    print(
        json.dumps(
            {
                k: summary[k]
                for k in ("phase", "collection_name", "stored_count", "queryable", "chunks_without_embedding")
            },
            indent=2,
        )
    )

    if not summary["stored_count"]:
        print("No vectors stored. Run phases 2 and 3 first.", file=sys.stderr)
        return 1
    if not summary["queryable"]:
        print("Chroma collection is not queryable after rebuild.", file=sys.stderr)
        return 1
    if summary["chunks_without_embedding"]:
        print("Some chunks were missing embeddings; they were skipped.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
