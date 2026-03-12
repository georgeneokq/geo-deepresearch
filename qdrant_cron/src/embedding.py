import os
from fastembed import TextEmbedding

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

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
