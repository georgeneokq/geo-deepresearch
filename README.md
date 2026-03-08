# Geo DeepResearch

Deep research implementation with a focus on targetted data scraping.

Each topic to be researched on will be broken up into subtasks.

Each subtask will have a category (e.g. cti, news, finance) and will be routed to a subagent which specializes in that field.

This structure allows for more targetted behaviour for each field, such as preferred sources for certain topics, without overloading the context of a single research agent.

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

### Build the container

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

## Challenges to tackle

- When multiple subagents of the same type are spawned, the current implementation has a high chance of causing repeated browsing of the same webpage.
- Right now, the child class doesn't do much other than provide sources to prioritize. Looking to find more use of this structure in the future.
- The intermediate summarization approach for dealing with megapages (very long webpages) is good for extracting pinpoint information (e.g. Listing IOCs of an APT). For long-form research, the intermediate summarization agent has been instructed to include specific quotes word-for-word if it is relevant to the query, but how well it works is not tested yet.
- Currently not providing google search geographic region as an option to the agent
