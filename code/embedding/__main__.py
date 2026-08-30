from __future__ import annotations

import argparse
import json
import sys

from embedding.pipeline import run_phase3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 3 embedding: Phase 2 chunks → data/embeddings/ via all-MiniLM-L6-v2.",
    )
    parser.add_argument(
        "--source-id",
        type=int,
        action="append",
        dest="source_ids",
        help="Embed only this source_id (repeatable). Default: all chunked sources.",
    )
    args = parser.parse_args(argv)

    if args.source_ids:
        for source_id in args.source_ids:
            if source_id < 1 or source_id > 25:
                print(f"source_id must be 1–25, got {source_id}", file=sys.stderr)
                return 2

    summary = run_phase3(source_ids=args.source_ids)
    print(
        json.dumps(
            {
                k: summary[k]
                for k in ("phase", "model", "embedding_dim", "embedded_chunk_count", "wrong_dim_chunk_ids")
            },
            indent=2,
        )
    )
    for row in summary["sources"]:
        print(f"  source {row['source_id']:02d}: {row['chunk_count']} chunks, dim {row['dim']}")

    if not summary["embedded_chunk_count"]:
        print("No Phase 2 chunks found under data/chunks/. Run phase 2 first.", file=sys.stderr)
        return 1
    if summary["wrong_dim_chunk_ids"]:
        print("Embeddings with wrong dimension detected. Aborting.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
