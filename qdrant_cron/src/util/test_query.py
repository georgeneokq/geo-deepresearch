import argparse
import asyncio
import os
from qdrant_client import AsyncQdrantClient
from util.logger import get_logger
from retrieval import query, get_enhanced_chunk_by_point_id

logger = get_logger()


async def test_search(query_text: str, *, client: AsyncQdrantClient):
    results = await query(query_text, client=client)

    print(f"\n--- Results for: '{query_text}' ---")
    for i, res in enumerate(results):
        if not res.payload:
            print("Unexpected point with no payload, skipping.")
            continue

        # print(res)
        enhanced_chunk_text = await get_enhanced_chunk_by_point_id(str(res.id), max_surrounding_character_count=500, client=client)
        print(f"{i+1}. Score: {res.score:.4f}")
        print(f"   File: {res.payload.get('file_name')}")
        print(f"   Chunk Index: {res.payload.get('chunk_index')}")
        print(f"   Chunk Content: {res.payload.get('text', "")}")
        print(f"   Enhanced Chunk: {enhanced_chunk_text}")
        print("-" * 20)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query the Qdrant document store.")
    parser.add_argument("query", type=str, help="The search query string.")
    parser.add_argument(
        "--url",
        default=os.environ.get("QDRANT_URL", "http://qdrant:6333"),
        help="Qdrant server URL (default: http://qdrant:6333)",
    )
    args = parser.parse_args()

    async def test():
        QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
        client = AsyncQdrantClient(url=QDRANT_URL)
        await test_search(args.query, client=client)
        await client.close()

    asyncio.run(test())
