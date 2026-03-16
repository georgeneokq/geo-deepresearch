import os

COLLECTION_NAME = os.environ.get("QDRANT_COLLECTION_NAME", "internal_docs")
WATCH_DIR = os.environ.get("INGEST_DIR", "/app/ingest_docs")
PROCESSED_DOCS_DIR = os.environ.get("PROCESSED_DIR", "/app/processed_docs")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
