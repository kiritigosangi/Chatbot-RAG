from __future__ import annotations

import argparse
import sys

from retrieval.pipeline import retrieve_for_query

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 5 retrieval: embed a question, query Chroma top-k, show chunks for inspection.",
    )
    parser.add_argument(
        "-q",
        "--query",
        action="append",
        dest="queries",
        help="A question to retrieve against (repeatable). If omitted, run the built-in sample set.",
    )
    parser.add_argument(
        "-k",
        "--top-k",
        type=int,
        default=5,
        help="Number of chunks to retrieve (default: 5).",
    )
    args = parser.parse_args(argv)

    queries = args.queries or [
        "What is the exit load for SBI Small Cap Fund?",
        "What is the TER / expense ratio of SBI Large Cap Fund?",
        "What is the lock-in period for SBI ELSS?",
        "What is the minimum SIP amount for SBI Flexicap Fund?",
        "What is the riskometer for SBI Midcap Fund?",
    ]

    exit_code = 0
    for question in queries:
        result = retrieve_for_query(question, k=args.top_k)
        _print_result(result)
        if result["coverage"] in ("no_coverage", "weak") or result["url_not_in_allowlist"]:
            exit_code = 1
    return exit_code


def _print_result(result: dict) -> None:
    scheme = result["scheme"] or "(none named)"
    print("=" * 78)
    print(f"Q: {result['question']}")
    print(f"  scheme detected : {scheme}")
    print(f"  coverage        : {result['coverage']}  (max_distance={result['max_distance']})")
    print(f"  ambiguous       : {result['ambiguous']}")
    print(f"  url_not_in_§9   : {result['url_not_in_allowlist']}")
    print("  top chunks:")
    for c in result["chunks"]:
        print(f"    - [{c['scheme']}/{c['doc_type']}] d={c['distance']} {c['url']}")
        print(f"      {c['text'][:120].strip().replace(chr(10), ' ')}")
        if c["document_date"]:
            print(f"      (document_date={c['document_date']})")


if __name__ == "__main__":
    raise SystemExit(main())
