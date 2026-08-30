"""Independent verification: reopen persisted Chroma store and query it.

Run: python verify_vector_db.py  (from Chatbot/)
"""

from __future__ import annotations

import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent / "code"
sys.path.insert(0, str(CODE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from embedding.model import embed_texts
from loading.paths import VECTOR_DB_DIR
from vector_store.store import COLLECTION_NAME, get_collection

if __name__ == "__main__":
    collection = get_collection()
    count = collection.count()
    print(f"collection={COLLECTION_NAME!r} count={count}")

    sample = "What is the exit load for SBI Small Cap Fund?"
    query = embed_texts([sample])[0]
    results = collection.query(query_embeddings=[query], n_results=3)
    print("query:", sample)
    for i, (doc, meta) in enumerate(
        zip(results["documents"][0], results["metadatas"][0])
    ):
        print(f"\n--- result {i+1} ---")
        print("text:", doc[:160].replace("\n", " "))
        print("url:", meta["url"])
        print("scheme:", meta["scheme"], "| doc_type:", meta["doc_type"])
