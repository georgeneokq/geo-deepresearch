import os
from uuid import UUID
from pathlib import Path
from qdrant_client import AsyncQdrantClient, models
from util.logger import get_logger
from embedding import (
    DENSE_EMBEDDING_MODEL,
    SPARSE_EMBEDDING_MODEL,
)
from extract import document_processor
from util.crypto import generate_file_sha256

logger = get_logger()

DOCS_DIR = os.environ.get("INGEST_DIR", "/app/ingest_docs")


async def get_point_by_id(
    point_id: str, *, client: AsyncQdrantClient, collection_name="internal_docs"
):
    """
    Gets text surrounding the chunk.

    Args:
        chunk_id (str): Chunk identifer, which will be used to identify the document and chunk location
    """
    points = await client.retrieve(
        collection_name=collection_name,
        ids=[point_id],
        with_payload=True,
        with_vectors=False,
    )

    if points:
        point = points[0]
        return point

    error_msg = f"Point {point_id} not found."
    logger.error(f"Warning: {error_msg}")
    raise RuntimeError(error_msg)


async def query(
    query_text: str, *, fetch_limit: int = 5, client: AsyncQdrantClient, collection_name="internal_docs"
):
    prefetch = [
        models.Prefetch(
            query=models.Document(text=query_text, model=DENSE_EMBEDDING_MODEL),
            limit=20,
        ),
        models.Prefetch(
            query=models.Document(text=query_text, model=SPARSE_EMBEDDING_MODEL),
            using="sparse-text",
            limit=20,
        ),
    ]

    # Search Qdrant
    results = (
        await client.query_points(
            collection_name=collection_name,
            limit=fetch_limit,
            prefetch=prefetch,
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            with_payload=True,
        )
    ).points

    return results


def get_surrounding_text(
    text_chunk: str,
    full_text: str,
    substring_index: int,
    max_surrounding_character_count: int,
):
    """
    While we can use the text_chunk to get substring index, we have already done this
    during ingestion, so we use that as the source of truth

    Returns:
        tuple[str, str, str]: Return tuple of (text_before, text, text_after)
    """
    # Max surrounding character count, applied for both before and after
    # Total is hence x2 of the value specified.
    text_before = full_text[
        max(0, substring_index - max_surrounding_character_count) : substring_index
    ]
    text_after = full_text[
        substring_index
        + len(text_chunk) : min(
            substring_index + len(text_chunk) + max_surrounding_character_count,
            len(full_text),
        )
    ]

    return (text_before, full_text, text_after)


async def get_surrounding_text_by_point_id(
    id: str | UUID,
    max_surrounding_character_count: int,
    *,
    client: AsyncQdrantClient,
    collection_name="internal_docs",
):
    """
    Calls get_surrounding_text, using point ID to retrieve all needed information.

    Returns:
        tuple[str, str, str]: Return tuple of (text_before, text, text_after)
    """
    point_id = str(id)
    point = await get_point_by_id(
        point_id, client=client, collection_name=collection_name
    )

    # Read the full document
    if not point.payload:
        raise RuntimeError("Unexpected empty payload in retrieved point")
    
    # Check the document exist and hash matches, if not raise error
    file_name = point.payload["file_name"]
    file_path = Path(DOCS_DIR, file_name)
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            file_hash = generate_file_sha256(file_bytes=file_bytes)

            # Check file hash matches
            # TODO: This can be averted 100% theoretically if we handle chunk deletion when original file is deleted off disk.
            if not file_hash == point.payload["file_hash"]:
                raise RuntimeError("Matching file name found, but file hash does not match. Aborting.")
    except FileNotFoundError:
        raise RuntimeError("File not found.")

    chunk_text = point.payload["text"]
    substring_index = point.payload["substring_index"]
    full_text = await document_processor.extract_markdown(file_path)

    text_before, text, text_after = get_surrounding_text(
        chunk_text,
        full_text,
        substring_index,
        max_surrounding_character_count=max_surrounding_character_count,
    )

    return (text_before, text, text_after)

async def get_enhanced_chunk_by_point_id(
    id: str | UUID,
    max_surrounding_character_count: int,
    *,
    client: AsyncQdrantClient,
    collection_name="internal_docs",
):
    text_before, text, text_after = await get_surrounding_text_by_point_id(
        id=id,
        max_surrounding_character_count=max_surrounding_character_count,
        client=client,
        collection_name=collection_name
    )

    return "".join((text_before, text, text_after))


def _sanitize_file_path(file_name: str, base_dir: str) -> Path:
    """
    Sanitize file path to prevent path traversal attacks.

    Args:
        file_name: The filename provided by user
        base_dir: The base directory that files must be within

    Returns:
        Resolved Path that is guaranteed to be within base_dir

    Raises:
        ValueError: If the resolved path is outside base_dir
    """
    base_path = Path(base_dir).resolve()
    # Join and resolve to get absolute normalized path
    file_path = (base_path / file_name).resolve()

    # Check that resolved path is within base directory
    try:
        file_path.relative_to(base_path)
    except ValueError:
        raise ValueError(f"Invalid file path: access denied")

    return file_path


async def get_document_text(file_name: str) -> str:
    """
    Read and extract text from a document.

    Args:
        file_name: Name of the file to read (must be within DOCS_DIR)

    Returns:
        Extracted text content from the document

    Raises:
        ValueError: If file path attempts path traversal
        FileNotFoundError: If file does not exist
    """
    # Sanitize path to prevent traversal attacks
    file_path = _sanitize_file_path(file_name, DOCS_DIR)

    # Extract and return text
    return await document_processor.extract_markdown(file_path)


async def get_document_text_by_point_id(
    point_id: str,
    *,
    client: AsyncQdrantClient,
    collection_name: str = "internal_docs",
) -> str:
    """
    Read and extract text from a document using a Qdrant point ID.

    The filename is retrieved from the point's payload, ensuring the file
    reference comes from indexed data rather than user input.

    Args:
        point_id: Qdrant point ID
        client: AsyncQdrantClient instance
        collection_name: Qdrant collection name

    Returns:
        Extracted text content from the document

    Raises:
        RuntimeError: If point not found, payload missing, or file not found
        ValueError: If file path attempts path traversal
    """
    # Retrieve point to get filename from payload
    point = await get_point_by_id(
        point_id, client=client, collection_name=collection_name
    )

    if not point.payload:
        raise RuntimeError("Point has empty payload")

    file_name = point.payload.get("file_name")
    if not file_name:
        raise RuntimeError("Point payload missing 'file_name'")

    # Read document using sanitized filename from payload
    return await get_document_text(file_name)
