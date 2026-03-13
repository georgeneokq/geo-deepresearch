import asyncio
import httpx
import os
from qdrant_client import AsyncQdrantClient, models
import uuid
from dataclasses import dataclass
from typing import Optional
import os
from extract import extract_text
from embedding import DENSE_EMBEDDING_MODEL, SPARSE_EMBEDDING_MODEL, preload_embedding_model, chunk_document, preload_sparse_embedding_model
from label import get_chunk_label
from util.logger import get_logger, setup_logging
from schemas import Chunk
from util.crypto import generate_file_sha256

setup_logging()

logger = get_logger()

# Configuration
COLLECTION_NAME = os.environ.get("QDRANT_COLLECTION_NAME", "internal_docs")
WATCH_DIR = os.environ.get("INGEST_DIR", "/app/ingest_docs")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")

client = AsyncQdrantClient(url=QDRANT_URL)

ingesting_files: set[str] = set()


@dataclass
class IngestedFile:
    file_name: str
    file_hash: str


type IngestedFilesCache = dict[str, IngestedFile]

ingested_files: IngestedFilesCache = {}



def generate_file_uuid(hash: str, index: int = 0):
    """
    Generates a deterministic UUID from a file hash and an optional index,
    where the index defaults to 0.
    """
    # Create a deterministic UUID from the hex digest
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{hash}_{index}"))


def get_file_cache_key(file_name: str, file_hash: str):
    return f"{file_name}_{file_hash}"


async def populate_ingested_files_cache(ingested_files_cache: IngestedFilesCache):
    """
    Retrieves all 'file_name' values from the collection payload.

    Args:
      ingested_files_set (dict[str, dict[str, Any]]): A dict to cache already ingested files
    """
    next_page = None

    total_points = 0
    total_files = 0

    while True:
        # "Scroll" through the points to get the metadata
        points, next_page = await client.scroll(
            collection_name=COLLECTION_NAME,
            limit=100,
            offset=next_page,
            with_payload=True,
            with_vectors=False,
        )

        for point in points:
            if point.payload and "file_name" in point.payload:
                # If the file is not yet encountered while scrolling, add it in.
                # Use hash as part of key
                file_name = point.payload["file_name"]
                file_hash = point.payload["file_hash"]
                key = get_file_cache_key(file_name, file_hash)
                if key not in ingested_files_cache:
                    ingested_files_cache[key] = IngestedFile(
                        file_name=file_name,
                        file_hash=file_hash,
                    )
                    total_files += 1

        total_points += len(points)

        if next_page is None:
            break

    logger.info(f"{total_files} files, {total_points} points loaded from Qdrant")


async def ingest_file(
    file_path: str,
    *,
    file_hash: Optional[str] = None,
    dense_model: str = DENSE_EMBEDDING_MODEL,
    sparse_model: str = SPARSE_EMBEDDING_MODEL
):
    """
    Ingest file at specified path.
    Currently only accepts pure text, PDF and docx documents.

    Args:
        file_path (str): Path of file to ingest
        file_hash (str): Skips calculation of sha256 if provided
        embedding_model (str): Text embedding model for ingestion
    """
    file_name = os.path.basename(file_path)

    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        # Extract text for different types of documents
        contents = extract_text(file_path=file_path)

        # File hash as secondary unique identifier
        hash = file_hash or generate_file_sha256(file_bytes=file_bytes)

        # Break file up into chunks.
        # Use document name as default label
        initial_chunks: list[Chunk] = [
            {
                "chunk": chunk,
                "start_index": start_index,
                "label": file_name
            }
            for chunk, start_index in chunk_document(contents, chunk_size=700)
        ]
        chunks: list[Chunk] = []

        if os.environ.get("ENABLE_DYNAMIC_CHUNK_LABELLING", "").lower() == "true":
            # To avoid rate limits, we run in sequence
            # TODO: Make parallelism a configurable option
            for chunk in initial_chunks:
                chunk_text = chunk["chunk"]
                logger.debug(f"Labelling chunk: {chunk_text[:150]}...")
                label = await get_chunk_label(chunk_text, contents, file_name)
                logger.debug(f"Labelled chunk: {chunk_text[:150]}...")
                chunks.append({
                    "label": label,
                    "start_index": chunk["start_index"],
                    "chunk": chunk_text
                })
        else:
            chunks = initial_chunks

        # Prepare points to ingest into Qdrant at once
        points = []

        for index, chunk in enumerate(chunks):
            # Define both dense and sparse vector for hybrid search; vector similarity + keyword search
            # Insert a labelled chunk as vector for boosting query accuracy, but only the raw chunk in the payload
            label = chunk["label"]
            chunk_text = chunk["chunk"]
            start_index = chunk["start_index"]
            labelled_chunk = f"**{label}**\n\n{chunk_text}"
            vector = {
                "": models.Document(text=labelled_chunk, model=dense_model),
                "sparse-text": models.Document(text=labelled_chunk, model=sparse_model),
            }

            # Generate metadata
            id = generate_file_uuid(hash, index)
            payload = {
                "file_name": file_name,
                "file_hash": hash,
                "chunk_index": index,
                "substring_index": start_index,
                "label": label,
                "text": chunk_text,
            }
            points.append(
                models.PointStruct(
                    id=id,
                    vector=vector,  # type:ignore
                    payload=payload
                )
            )

        # Upsert to qdrant
        await client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
        )
    except Exception as e:
        logger.error(f"Failed to ingest {file_name}: {e}")


async def init_qdrant():
    # Check if collection exists
    exists = await client.collection_exists(COLLECTION_NAME)

    if not exists:
        dense_embedding_size = int(os.environ.get("DENSE_EMBEDDING_SIZE", 384))
        print(f"Creating collection: {COLLECTION_NAME}")
        await client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=dense_embedding_size,
                distance=models.Distance.COSINE,
            ),
            # Sparse Vector Config (Keyword-based)
            sparse_vectors_config={
                "sparse-text": models.SparseVectorParams(
                    index=models.SparseIndexParams(on_disk=True)
                )
            },
        )

        # Pro-tip: Create an index on file_name for faster lookups
        await client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="file_name",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )


async def check_and_sync(
    *, docs_dir: str = WATCH_DIR, ingested_files_cache: IngestedFilesCache
):
    """Check for new files and ingest"""
    # Scan directory for new docs
    local_files = [
        f for f in os.listdir(docs_dir) if os.path.isfile(os.path.join(docs_dir, f))
    ]

    # Find files that haven't been processed
    for file_name in local_files:
        file_path = os.path.join(WATCH_DIR, file_name)

        # Get key for caching
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        file_hash = generate_file_sha256(file_bytes=file_bytes)

        cache_key = get_file_cache_key(os.path.basename(file_path), file_hash)

        if file_name not in ingesting_files and file_name not in ingested_files_cache:
            ingesting_files.add(cache_key)
            try:
                # Ingest and add to cache
                logger.debug(f"Ingesting: {file_path}")
                await ingest_file(file_path, file_hash=file_hash)
                ingested_files[file_name] = IngestedFile(
                    file_name=file_name,
                    file_hash=file_hash,
                )
            except Exception as e:
                logger.error(f"Failed to ingest {file_path}: {e}")
            finally:
                ingesting_files.remove(cache_key)


async def wait_for_qdrant_startup():
    async with httpx.AsyncClient() as client:
        while True:
            try:
                response = await client.get(f"{QDRANT_URL}/readyz", timeout=1.0)
                if response.status_code == 200:
                    logger.debug("Qdrant is ready!")
                    break
                await asyncio.sleep(1)
            except (httpx.ConnectError, httpx.TimeoutException):
                pass


def preload_models():
    preload_sparse_embedding_model()
    preload_embedding_model()


async def main():
    # Check qdrant is ready
    await wait_for_qdrant_startup()

    # Initialize collection in qdrant
    init_db_task = asyncio.create_task(init_qdrant())

    # Preload embedding model while qdrant is initializing
    preload_models()

    # Wait for qdrant to be initialized
    await init_db_task

    logger.debug("Checking for new files...")

    # Populate ingested files cache
    await populate_ingested_files_cache(ingested_files_cache=ingested_files)

    # Watch for new files
    logger.info(f"Watching for files to ingest in {WATCH_DIR}")
    while True:
        try:
            await check_and_sync(ingested_files_cache=ingested_files)
        except Exception as e:
            logger.error(f"Error: {e}")

        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
