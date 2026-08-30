from __future__ import annotations

import argparse
import json
import sys

from loading.pipeline import run_phase1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 1 data loading: closed 25-URL corpus into data/raw and data/skips.",
    )
    parser.add_argument(
        "--source-id",
        type=int,
        action="append",
        dest="source_ids",
        help="Load only this source_id (repeatable). Default: all 1–25.",
    )
    parser.add_argument(
        "--uploads-only",
        action="store_true",
        help="Do not fetch. Use data/uploads/{id}.html|.pdf only.",
    )
    args = parser.parse_args(argv)

    if args.source_ids:
        for source_id in args.source_ids:
            if source_id < 1 or source_id > 25:
                print(f"source_id must be 1–25, got {source_id}", file=sys.stderr)
                return 2

    summary = run_phase1(source_ids=args.source_ids, uploads_only=args.uploads_only)
    print(json.dumps({k: summary[k] for k in ("phase", "ingest_at", "ok", "skipped")}, indent=2))
    for record in summary["records"]:
        status = record["status"]
        extra = record.get("skip_reason") or f"{record.get('raw_text_chars', 0)} chars"
        print(f"  [{status}] {record['source_id']:02d} {record['url']} ({extra})")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
