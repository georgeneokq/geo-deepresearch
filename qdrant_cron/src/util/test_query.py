import argparse
import asyncio
import os
from qdrant_client import AsyncQdrantClient, models
from embedding import DENSE_EMBEDDING_MODEL, SPARSE_EMBEDDING_MODEL

async def test_search(query_text: str, *, client: AsyncQdrantClient):
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
    results = (await client.query_points(
        collection_name="internal_docs",
        limit=5,
        prefetch=prefetch,
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        with_payload=True
    )).points

    print(f"\n--- Results for: '{query_text}' ---")
    for i, res in enumerate(results):
        if not res.payload:
            print("Unexpected point with no payload, skipping.")
            continue

        # print(res)
        print(f"{i+1}. Score: {res.score:.4f}")
        print(f"   File: {res.payload.get('file_name')}")
        print(f"   Chunk Index: {res.payload.get('chunk_index')}")
        print(f"   Chunk Content: {res.payload.get('text', "")}")
        print("-" * 20)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query the Qdrant document store.")
    parser.add_argument("query", type=str, help="The search query string.")
    parser.add_argument(
        "--url", 
        default=os.environ.get("QDRANT_URL", "http://qdrant:6333"),
        help="Qdrant server URL (default: http://qdrant:6333)"
    )
    args = parser.parse_args()

    async def test():
        QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
        client = AsyncQdrantClient(url=QDRANT_URL)
        await test_search(args.query, client=client)
        await client.close()
    
    asyncio.run(test())
