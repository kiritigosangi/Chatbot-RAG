from __future__ import annotations

import argparse
import json
import sys

from chunking.pipeline import run_phase2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 2 chunking: Phase 1 ok records → data/chunks/ (MiniLM-sized, URL on every chunk).",
    )
    parser.add_argument(
        "--source-id",
        type=int,
        action="append",
        dest="source_ids",
        help="Chunk only this source_id (repeatable). Default: all ok Phase 1 records.",
    )
    args = parser.parse_args(argv)

    if args.source_ids:
        for source_id in args.source_ids:
            if source_id < 1 or source_id > 25:
                print(f"source_id must be 1–25, got {source_id}", file=sys.stderr)
                return 2

    summary = run_phase2(source_ids=args.source_ids)
    print(
        json.dumps(
            {
                k: summary[k]
                for k in (
                    "phase",
                    "ok_sources",
                    "chunk_count",
                    "oversize_chunk_ids",
                    "url_not_in_allowlist_chunk_ids",
                )
            },
            indent=2,
        )
    )
    for row in summary["sources"]:
        print(f"  source {row['source_id']:02d}: {row['chunk_count']} chunks ({row['url']})")

    if not summary["ok_sources"]:
        print("No Phase 1 ok records found under data/raw/text/. Run phase 1 first.", file=sys.stderr)
        return 1
    if summary["oversize_chunk_ids"] or summary["url_not_in_allowlist_chunk_ids"] or summary["missing_url_chunk_ids"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
