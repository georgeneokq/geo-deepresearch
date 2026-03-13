import os
from fastembed import TextEmbedding, SparseTextEmbedding
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path

MODELS_DIR = os.environ.get("MODELS_DIR", "/app/models")

DENSE_EMBEDDING_MODEL = os.environ.get(
    "DENSE_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)

SPARSE_EMBEDDING_MODEL = os.environ.get("SPARSE_EMBEDDING_MODEL", "Qdrant/bm25")

DENSE_EMBEDDING_MODEL_PATH = Path(MODELS_DIR, DENSE_EMBEDDING_MODEL)
SPARSE_EMBEDDING_MODEL_PATH = Path(MODELS_DIR, SPARSE_EMBEDDING_MODEL)


def preload_sparse_embedding_model(
    embedding_model: str = SPARSE_EMBEDDING_MODEL,
    cache_dir=MODELS_DIR,
    local_files_only: bool = False,
):
    SparseTextEmbedding(
        model_name=embedding_model,
        cache_dir=cache_dir,
        local_files_only=local_files_only,
    )
    print(f"Loaded sparse text embedding model: {embedding_model}")


def preload_embedding_model(
    embedding_model: str = DENSE_EMBEDDING_MODEL,
    cache_dir: str = MODELS_DIR,
    local_files_only: bool = False,
):
    TextEmbedding(
        model_name=embedding_model,
        cache_dir=cache_dir,
        local_files_only=local_files_only,
    )
    print(f"Loaded dense text embedding model: {embedding_model}")


def embed_text(text: str, embedding_model: str = DENSE_EMBEDDING_MODEL):
    """
    Embed text using specified embedding model
    """
    model = TextEmbedding(model_name=embedding_model)
    vector = list(model.embed([text]))[0]
    return vector


def chunk_document(text: str, chunk_size: int = 800, overlap_ratio: float = 0.1):
    """
    Chunks documents for vector DBs.
    Returns a list of tuples.
    [0] (str):  Text chunk
    [1] (int):  Text chunk start index relative to the original document's
                text context returned from `extract_text`
    """
    chunk_overlap = int(chunk_size * overlap_ratio)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        strip_whitespace=False,
    )

    chunks = splitter.split_text(text)
    start_indexes = [text.index(chunk) for chunk in chunks]

    # Filter out chunks that are too short
    return [
        (chunk, start_index)
        for chunk, start_index in zip(chunks, start_indexes)
        if len(chunk.strip()) > 5
    ]
