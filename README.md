# Geo DeepResearch

Deep research implementation with a focus on targetted data scraping.

Each topic to be researched on will be broken up into subtasks.

Each subtask will have a category (e.g. cti, news, finance) and will be routed to a subagent which specializes in that field.

This structure allows for more targetted behaviour for each field, such as preferred sources for certain topics, without overloading the context of a single research agent.

If there are preferred sources specified for a certain category, these sources will be used to search google using the advanced search operator "site".
(e.g. site:cloud.google.com IOCs of APT33)

As agents may be running in parallel and may browse the same website at the same time, mutex is used to prevent them from doing double work.
If an agent wants to browse a webpage, the agent will first have to read from cache.
If the cache is empty for the specified URL, the agent will try to acquire a lock for that URL.
If a lock for that URL already exists and is acquired, it will wait for the lock to be released, then check the cache again.
If the cache is empty, perhaps due to website browse failure on the other agent's side, the current agent will try to browse it.

## Setup

### Download tokenizer

This deep research system uses tokenizer for optimization.
Download the tokenizer files using `scripts/download_tokenizer.py`.
It uses the transformers library, you can use `uv` package manager to prevent polluting your system environment.

```bash
uv run --with transformers scripts/download_tokenizer.py zai-org/GLM-4.7-Flash
```

After it is installed, move the entire folder containing the tokenizer files into the root directory, and rename it to `tokenizer`.

This folder will be volumed into the container, if you wish to modify this you have to change the volume and env var.

### Folder for internal docs ingestion

We use Qdrant for internal docs ingestion and querying. Set up the folder to drop docs into:

```bash
mkdir -p qdrant_cron/ingest_docs
```

### Build the containers

```bash
docker compose build
```

## Run the API server

```bash
docker compose up -d
```

## Testing

Tests will be ran inside Docker container.

Run all unit tests:
```bash
docker compose exec -it -w /app api-server uv run pytest -s -v -m "unit" tests/
```

Run all integration tests:
```bash
docker compose exec -it -w /app api-server uv run pytest -s -v -m "integration" tests/
```

Run all e2e tests:
```bash
docker compose exec -it -w /app api-server uv run pytest -s -v -m "e2e" tests/
```

### Qdrant

To test querying Qdrant for internal docs, ensure the qdrant_cron container is up, then run:

```bash
docker compose exec -it qdrant_cron python -m util.test_query "What is the guest subnet in Amaris.AI?"
```

## Challenges to tackle

- Right now, the child class doesn't do much other than provide sources to prioritize. Looking to find more use of this structure in the future.
- The intermediate summarization approach for dealing with megapages (very long webpages) is good for extracting pinpoint information (e.g. Listing IOCs of an APT). For long-form research, the intermediate summarization agent has been instructed to include specific quotes word-for-word if it is relevant to the query, but how well it works is not tested yet.
- Currently not providing google search geographic region as an option to the agent
- Currently only caching content, but the same lock and cache can be used for storing the summary as well. This saves even more calls
- Current browse retry logic retries up to 3 times no matter what the error code is. This doesn't make sense for 402 (Payment Required) for example.
- Jina started returning 402 payment required for many websites in one of my runs but when manually browsing to that URL it is publicly accessible. Checking rate limit of Jina API key with "curl https://r.jina.ai -H "Authorization: Bearer <API_KEY>" showed negative balance, further proving it is indeed Jina's rate limit

## TODO

- Local document searching
- Reduce reliance on Jina: Build custom scraper using httpx
1. Scrape using httpx
2. Check if content contains any word in the query to detect dynamic JS pages
3. If word contained, assume scrape was successful. If not, scrape using Playwright.
4. Pass raw HTML to python-readability -> trafilatura
5. Pass that into summarize function

