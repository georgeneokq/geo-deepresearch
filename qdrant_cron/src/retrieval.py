import os
from uuid import UUID
from pathlib import Path
from qdrant_client import AsyncQdrantClient, models
from util.logger import get_logger
from embedding import (
    DENSE_EMBEDDING_MODEL,
    SPARSE_EMBEDDING_MODEL,
)
from extract import extract_text
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
    query_text: str, *, client: AsyncQdrantClient, collection_name="internal_docs"
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
            limit=5,
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
    full_text = extract_text(file_bytes=file_bytes)

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
