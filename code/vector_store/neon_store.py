"""Neon (PostgreSQL + pgvector) vector store for Phase 4/5.

Replaces the local Chroma persistence for serverless (Vercel) deployment:

  - a single `chunks` relation holds text + metadata + a `vector(384)` column
  - cosine distance (`<=>`) matches the cosine HNSW space Chroma used, so
    coverage thresholds and ranking behave the same for the MiniLM vectors
  - `load_jsonl(...)` bulk-populates from the Phase 2/3 sidecars
    (data/chunks/x.json + data/embeddings/x.json) used by the local path
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from config import database_url
from loading.paths import (
    CHUNKS_DIR,
    CHATBOT_ROOT,
    EMBEDDINGS_DIR,
    SOURCE_STEM,
)

EMBEDDING_DIM = 384
TABLE = "chunks"

SCHEMA_SQL = f"""
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS {TABLE} (
    chunk_id      TEXT PRIMARY KEY,
    text          TEXT NOT NULL,
    url           TEXT NOT NULL,
    source_id     INTEGER NOT NULL,
    scheme        TEXT NOT NULL,
    doc_type      TEXT NOT NULL,
    ingest_at     TEXT,
    document_date TEXT,
    embedding     vector({EMBEDDING_DIM}) NOT NULL
);
CREATE INDEX IF NOT EXISTS {TABLE}_embedding_hnsw
    ON {TABLE} USING hnsw (embedding vector_cosine_ops);
"""

COUNT_SQL = f"SELECT COUNT(*) FROM {TABLE}"


def connect():
    url = database_url()
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set for Neon storage. Add it to .env (or Render env)."
        )
    import psycopg

    # Neon connection pools use PgBouncer in transaction mode, which does not
    # support server-side prepared statements. Disabling prepare_threshold makes
    # psycopg issue client-side only, so it works through the -pooler endpoint.
    return psycopg.connect(url, prepare_threshold=None)


def init_schema(*, drop: bool = False) -> None:
    """Create the pgvector extension, table, and index. Optionally wipe rows."""
    with connect() as conn:
        with conn.cursor() as cur:
            if drop:
                cur.execute(f"DROP TABLE IF EXISTS {TABLE} CASCADE")
            cur.execute(SCHEMA_SQL)
        conn.commit()


def count() -> int:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(COUNT_SQL)
            return int(cur.fetchone()[0])


def _pair_rows(source_id: int) -> list[dict[str, Any]]:
    """Join a source's chunk records with its embedding sidecar."""
    chunks = json.loads(
        (CHUNKS_DIR / f"{source_id:02d}.json").read_text(encoding="utf-8")
    )
    vec_path = EMBEDDINGS_DIR / f"{SOURCE_STEM.format(source_id=source_id)}.json"
    vectors = {}
    if vec_path.exists():
        vectors = {
            entry["chunk_id"]: entry["vector"]
            for entry in json.loads(vec_path.read_text(encoding="utf-8"))
        }
    rows: list[dict[str, Any]] = []
    for c in chunks:
        vec = vectors.get(c["chunk_id"])
        if vec is None:
            continue
        rows.append(
            {
                "chunk_id": c["chunk_id"],
                "text": c["text"],
                "url": c["url"],
                "source_id": int(c["source_id"]),
                "scheme": c["scheme"],
                "doc_type": c["doc_type"],
                "ingest_at": c.get("ingest_at"),
                "document_date": c.get("document_date"),
                "embedding": vec,
            }
        )
    return rows


INSERT_SQL = f"""
INSERT INTO {TABLE}
    (chunk_id, text, url, source_id, scheme, doc_type, ingest_at, document_date, embedding)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
ON CONFLICT (chunk_id) DO NOTHING;
"""


def load_from_sidecars(*, source_ids: list[int] | None = None) -> dict[str, Any]:
    """Populate Neon from the same data/chunks + data/embeddings sidecars."""
    wanted = set(source_ids) if source_ids is not None else None
    chunk_files = sorted(CHUNKS_DIR.glob("[0-9][0-9].json"))
    files = [p for p in chunk_files if wanted is None or int(p.stem) in wanted]

    loaded = 0
    with connect() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                INSERT_SQL,
                [
                    (
                        r["chunk_id"],
                        r["text"],
                        r["url"],
                        r["source_id"],
                        r["scheme"],
                        r["doc_type"],
                        r["ingest_at"],
                        r["document_date"],
                        json.dumps(r["embedding"]),
                    )
                    for f in files
                    for r in _pair_rows(int(f.stem))
                ],
            )
        conn.commit()
        loaded = count()

    return {
        "phase": "neon-load",
        "sources_loaded": len(files),
        "rows_in_table": loaded,
        "host": _host_hint(),
    }


def _host_hint() -> str:
    url = database_url() or ""
    return url.split("@")[-1].split("/")[0][:60]


QUERY_SQL = f"""
SELECT chunk_id, text, url, source_id, scheme, doc_type, ingest_at,
       document_date, embedding <=> %s::vector AS distance
FROM {TABLE}
"""


def query_top_k(
    query_vector: list[float],
    *,
    k: int,
    scheme: str | None = None,
) -> list[dict[str, Any]]:
    """Return the nearest k chunks by cosine distance, optionally scheme-filtered."""
    sql = QUERY_SQL
    params: list[Any] = [json.dumps(query_vector)]
    if scheme is not None:
        sql += " WHERE scheme = %s"
        params.append(scheme)
    sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
    params.append(json.dumps(query_vector))
    params.append(int(k))

    results: list[dict[str, Any]] = []
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            for row in cur.fetchall():
                results.append(
                    {
                        "chunk_id": row[0],
                        "text": row[1],
                        "url": row[2],
                        "source_id": row[3],
                        "scheme": row[4],
                        "doc_type": row[5],
                        "ingest_at": row[6],
                        "document_date": row[7],
                        "distance": round(float(row[8]), 4),
                    }
                )
    return results
