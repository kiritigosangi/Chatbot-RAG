"""Phase 1 writes only under Chatbot/data/."""

from __future__ import annotations

from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[1]
CHATBOT_ROOT = CODE_DIR.parent
DATA_DIR = CHATBOT_ROOT / "data"

UPLOADS_DIR = DATA_DIR / "uploads"
RAW_HTML_DIR = DATA_DIR / "raw" / "html"
RAW_PDF_DIR = DATA_DIR / "raw" / "pdf"
RAW_TEXT_DIR = DATA_DIR / "raw" / "text"
SKIPS_DIR = DATA_DIR / "skips"
CHUNKS_DIR = DATA_DIR / "chunks"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"
VECTOR_DB_DIR = DATA_DIR / "vector_db"

SOURCE_STEM = "{source_id:02d}"


def ensure_data_dirs() -> None:
    for path in (
        UPLOADS_DIR,
        RAW_HTML_DIR,
        RAW_PDF_DIR,
        RAW_TEXT_DIR,
        SKIPS_DIR,
        CHUNKS_DIR,
        EMBEDDINGS_DIR,
        VECTOR_DB_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def upload_candidates(source_id: int) -> list[Path]:
    """Builder files mapped to a source_id: 01.pdf, 1.html, 01.htm, etc."""
    stems = (f"{source_id:02d}", str(source_id))
    suffixes = (".pdf", ".html", ".htm")
    found: list[Path] = []
    for stem in stems:
        for suffix in suffixes:
            path = UPLOADS_DIR / f"{stem}{suffix}"
            if path.is_file():
                found.append(path)
    return found
