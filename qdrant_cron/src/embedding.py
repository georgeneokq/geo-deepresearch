import os
from fastembed import TextEmbedding, SparseTextEmbedding
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    ExperimentalMarkdownSyntaxTextSplitter
)
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


# TODO: Make these configurable. Defaults are currently optimized for bge-large-en-v1.5 embedding model
def chunk_document(text: str, chunk_size: int = 1500, overlap_ratio: float = 0.1) -> list[tuple[str, int]]:
    """
    Chunks documents for vector DBs.
    Assumes that the documents have been converted to markdown; the chunking will use markdown strategy.
    Returns a list of tuples.
    [0] (str):  Text chunk
    [1] (int):  Text chunk start index relative to the original document's
                text context returned from `document_processor.extract_markdown`
    """
    # strip_headers=False ensures the section text is still an exact substring of the original document
    # Cannot use MarkdownHeaderTextSplitter as it does not retain original text as is
    header_splitter = ExperimentalMarkdownSyntaxTextSplitter(
        headers_to_split_on=[
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Section"),
        ],
        strip_headers=False,
    )

    sections = header_splitter.split_text(text)

    chunk_overlap = int(chunk_size * overlap_ratio)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,  # Calculates index relative to the SECTION
        separators=[
            "\n\n# ",  # Double newline + H1
            "\n\n## ",  # Double newline + H2
            "\n\n### ",  # Double newline + H3
            "\n# ",  # Single newline + H1
            "\n## ",  # Single newline + H2
            "\n### ",  # Single newline + H3
            "\n\n",  # Paragraphs
            "\n|",  # Table Rows
            "\n",  # Lines
            " ",
            "",
        ],
        strip_whitespace=False,
    )

    final_chunks_with_indices: list[tuple[str, int]] = []

    # print("ORIGINAL\n")
    # print(text)
    # print("\n---------------------------------")

    for section in sections:
        # Find the absolute start position of this section in the original text
        # Because we used strip_headers=False, this will be a perfect match
        section_base_index = text.find(section.page_content)

        # Sub-split the section into model-sized chunks
        sub_documents = text_splitter.split_documents([section])

        for sub_doc in sub_documents:
            # Calculate global index: Section Start + Chunk Offset within Section
            local_start_index = sub_doc.metadata.get("start_index", 0)
            global_start_index = section_base_index + local_start_index

            chunk_text = sub_doc.page_content

            # Filter out chunks that are effectively empty/noise
            if len(chunk_text.strip()) > 5:
                final_chunks_with_indices.append((chunk_text, global_start_index))

    return final_chunks_with_indices
