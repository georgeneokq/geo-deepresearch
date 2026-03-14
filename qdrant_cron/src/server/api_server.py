import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, HTTPException
from qdrant_client import AsyncQdrantClient

from util.logger import setup_logging, get_logger
from retrieval import query as query_qdrant, get_document_text_by_point_id

# Logger setup
API_SERVER_LOGGER_NAME = "qdrant_api"
setup_logging(API_SERVER_LOGGER_NAME)
logger = get_logger(API_SERVER_LOGGER_NAME)

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "internal_docs")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting up API server...")
    client = AsyncQdrantClient(url=QDRANT_URL)
    app.state.qdrant_client = client
    yield
    # Shutdown
    logger.info("Shutting down API server...")
    await client.close()


app = FastAPI(
    title="Qdrant Retriever API",
    description="API server for Qdrant Cron service",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/query")
async def query_endpoint(
    query: str = Query(..., description="Text to search for"),
    limit: int = Query(default=5, ge=1, le=50, description="Max number of results"),
    collection_name: str = Query(
        default=COLLECTION_NAME, description="Qdrant collection name"
    ),
) -> list[dict]:
    """Query the Qdrant vector store for similar documents."""
    client: AsyncQdrantClient = app.state.qdrant_client
    results = await query_qdrant(
        query_text=query, fetch_limit=limit, client=client, collection_name=collection_name
    )
    return [
        {"id": str(point.id), "score": point.score, "payload": point.payload}
        for point in results
    ]


@app.get("/documents/{point_id}")
async def get_document(point_id: str) -> dict[str, str]:
    """Get full text content of a document using its Qdrant point ID."""
    client: AsyncQdrantClient = app.state.qdrant_client
    try:
        text = await get_document_text_by_point_id(point_id, client=client)
        return {"point_id": point_id, "content": text}
    except (RuntimeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
