FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STORAGE=neon \
    EMBEDDING_BACKEND=fastembed

WORKDIR /app

# System libs needed by onnxruntime/fastembed at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Runtime-only Python deps (the live app needs Streamlit + Neon + fastembed,
# not the local ingest stack: torch / transformers / chromadb).
COPY requirements-deploy.txt .
RUN pip install --upgrade pip && pip install -r requirements-deploy.txt

# Application code.
COPY code ./code
COPY run_ui.py ./

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD \
  python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health')"

CMD ["python", "run_ui.py"]
