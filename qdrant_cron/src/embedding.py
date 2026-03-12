import os
from fastembed import TextEmbedding
from langchain_text_splitters import RecursiveCharacterTextSplitter

EMBEDDING_MODEL = os.environ.get(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)


def preload_embedding_model(embedding_model: str = EMBEDDING_MODEL):
    print(f"Pre-loading embedding model {embedding_model}...")
    TextEmbedding(model_name=embedding_model)
    print("Model loaded and ready.")


def embed_text(text: str, embedding_model: str = EMBEDDING_MODEL):
    """
    Embed text using specified embedding model
    """
    model = TextEmbedding(model_name=embedding_model)
    vector = list(model.embed([text]))[0]
    return vector


def chunk_document(text: str, chunk_size: int = 800, overlap_ratio: float = 0.1):
    """
    Chunks documents for vector DBs.
    """
    chunk_overlap = int(chunk_size * overlap_ratio)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_text(text)

    # Filter out chunks that are too short
    return [chunk for chunk in chunks if len(chunk.strip()) > 5]
