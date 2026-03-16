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

## Challenges

- Current architecture disallows browsing of same source twice. This is flawed as the contents returned from browsing a page can be different, as we are not working with the raw webpage content the form the report, but rather a summary of what is relevant to the deep research topic. We should still keep track of the sources browsed, but instead of enforcing that a webpage / document cannot be browsed twice, we make sure a document-query pair cannot be repeated twice. Especially in the context of internal docs RAG, paraphrasing may help capture high-scoring chunks that weren't captured in previous queries.
- Current markdown chunking approach takes headers as a chunk on its own, this makes irrelevant chunks "## MITRE ATT&amp;CK Tactics and Techniques"
- Docling returns broken tables when spanning across multi-page, this causes difficulty for LLM to understand
- Currently reads whole document if more than 2 chunks score at least 0.4, but this should be dynamically adjusted according to page size / character count