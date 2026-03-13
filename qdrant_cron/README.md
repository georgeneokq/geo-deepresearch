## Setup

uv run --with transformers scripts/download_tokenizer.py BAAI/bge-large-en-v1.5
uv run --with transformers scripts/download_tokenizer.py Qdrant/bm25

To test querying Qdrant for internal docs, ensure the qdrant_cron container is up, then run:

```bash
docker compose exec -it qdrant_cron python -m util.test_query "What is the guest subnet in Amaris.AI?"
```

## TODO

Read embedding models from local files instead of downloading upon every container creation.
To be reused for qdrant api server.
Currently not a huge problem because download is pretty fast.
