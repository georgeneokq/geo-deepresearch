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

## Architecture & Flow

This section details the complete flow from when the API server receives a query until the final summary is outputted.

### 1. API Request Handling (`main.py`)

When a POST request is made to `/research`:

```json
{
  "query": "Research topic here",
  "mode": "hybrid"  // Options: "internet", "internal", "hybrid"
}
```

The request is processed as follows:

1. **Mode Validation**: The `mode` string is validated and converted to a `ResearchMode` enum
2. **Query Decomposition**: The query is sent to an LLM which breaks it into subqueries with expertise categories (e.g., "cti", "finance", "general")
3. **Agent Creation**: For each subquery, a specialized subagent is created:
   - `CtiAgentRunner`: Cyber threat intelligence, prioritizes sources like cloud.google.com for IOCs
   - `GeneralAgentRunner`: General research topics
   - Each agent receives the research mode configuration
4. **Parallel Execution**: All subagents run in parallel (or sequentially based on `parallel_mode` config)
5. **Final Summarization**: Results from all agents are merged into a final report

### 2. Research Modes

The system supports three research modes:

| Mode | Description | Use Case |
|------|-------------|----------|
| **internet** | Web search + webpage browsing only | General research, current events |
| **internal** | Qdrant document search + retrieval only | Internal knowledge base queries |
| **hybrid** (default) | Both internet and internal in sequence | Comprehensive research |

### 3. Subagent Research Loop

Each subagent runs an independent research loop with the following phases:

#### Phase A: Internet Research (if mode is "internet" or "hybrid")

1. **Priority Source Check**: If the agent has priority sources (e.g., CTI agent has `cloud.google.com`), these are searched first using `site:` operator
2. **Web Search**: LLM generates search queries, calls Serper API (Google Search)
3. **Webpage Browsing**: LLM selects top URLs from search results, retrieves content via Jina AI
4. **Summarization**: New content is summarized and merged with existing summary
5. **Repeat**: Continue until `source_limit` is reached (default: 5-6 sources)

#### Phase B: Internal Research (if mode is "internal" or "hybrid")

1. **Qdrant Query**: LLM generates search query, calls Qdrant API server
2. **Score-Based Strategy**:
   - **High confidence** (avg score > 0.5): Read full documents (top 3 files)
   - **Low confidence** (avg score ≤ 0.5): Read surrounding chunks for high-scoring points (one chunk per file)
3. **Document Retrieval**: Fetch content from Qdrant API
4. **Summarization**: Content is summarized with file name tracking for citations
5. **Repeat**: Continue until all unique files are retrieved or `source_limit` is reached

**Key Difference from Internet Research**: Internal research tracks unique files by `file_hash` to prevent re-retrieving the same document. The loop exits gracefully when no more unique files are available.

### 4. Concurrency Control: BrowseManager & InternalBrowseManager

To prevent duplicate work when multiple agents run in parallel:

#### BrowseManager (Web Pages)

```
Agent A wants to browse URL X
    ↓
Check cache for URL X
    ↓
Cache miss → Try to acquire lock for URL X
    ↓
┌─────────────────────────────────────┐
│ If parallel_mode = false:           │
│   - Acquire global master lock      │
│   - Only ONE agent browses at a time│
│                                     │
│ If parallel_mode = true:            │
│   - Acquire per-URL lock            │
│   - Multiple agents can browse      │
│     different URLs simultaneously   │
└─────────────────────────────────────┘
    ↓
Browse URL via Jina AI
    ↓
Store result in cache
    ↓
Release lock
```

**Key Features**:
- **Cache invalidation**: Cached items expire after 60 seconds
- **Lock timeout**: 60 seconds to prevent deadlocks
- **Retry logic**: If lock acquisition fails, agent waits and retries (max 2 attempts)
- **Default**: `parallel_mode = false` to avoid rate limits on Jina/Serper APIs

#### InternalBrowseManager (Qdrant Documents)

Same pattern as BrowseManager but for internal document retrieval:
- Per-point-ID locking when `parallel_mode = true`
- Global lock when `parallel_mode = false`
- Content caching to prevent duplicate Qdrant API calls

### 5. Internal Document Processing (Qdrant)

#### Ingestion Pipeline (qdrant_cron service)

```
Document dropped into qdrant_cron/ingest_docs/
    ↓
Cron job detects new file
    ↓
Extract text (pdfplumber, python-docx, etc.)
    ↓
Split into chunks (~500 chars each)
    ↓
Generate embeddings:
  - Dense: BAAI/bge-m3
  - Sparse: BAAI/bge-m3 sparse
    ↓
Store in Qdrant with metadata:
  - file_name, file_hash (SHA256)
  - chunk_index, substring_index
  - text content
```

#### Query Pipeline

```
Agent queries Qdrant API: GET /query?query=<search_text>&limit=20
    ↓
Qdrant performs hybrid search:
  - Dense vector similarity
  - Sparse vector (keyword) match
  - Fusion: Reciprocal Rank Fusion (RRF)
    ↓
Returns list of points with scores:
[
  {
    "id": "uuid",
    "score": 0.83,
    "payload": {
      "file_name": "doc.pdf",
      "file_hash": "sha256...",
      "text": "chunk content"
    }
  }
]
    ↓
Group by file_hash:
  - Sum scores for all chunks from same file
  - Calculate average score per file
  - Track first point_id for each file
    ↓
Apply retrieval strategy based on average score
```

#### Chunking Strategies

**For Megapages (>10,000 tokens)**:
```
Raw content → Semantic chunker (7000 tokens/chunk, 500 overlap)
    ↓
Each chunk summarized independently (1000 token budget)
    ↓
Intermediate summaries concatenated
    ↓
Final summarization pass
```

**For Internal Documents (Low Confidence)**:
```
Retrieve surrounding text chunk:
  - Center: Matching chunk text
  - Before: Up to 500 characters preceding
  - After: Up to 500 characters following
    ↓
Summarize with standard budget
```

### 6. Citation Formatting

Internal documents use a standardized citation format:

```
In-text: APT42 uses NICECURL backdoor [1]

References:
1. Internal docs - APT42s recent activity.pdf
2. https://cloud.google.com/blog/...
```

File names are tracked during retrieval and passed to the summarizer for proper formatting.

### 7. Token Budget Management

To prevent context overflow:

- **Per-summary budget**: Calculated dynamically based on remaining tokens
- **Buffer**: 200 words reserved for safety
- **Minimum room**: 150 tokens always kept available
- **Chunking threshold**: 10,000 tokens triggers semantic chunking
- **Final summary limit**: 80% of model's max tokens (`MODEL_MAX_TOKENS * 4/5`)

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    POST /research                               │
│                  {query, mode: "hybrid"}                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  1. Decompose Query (LLM)                                       │
│     "APT42 cyber incidents" →                                   │
│     [{"query": "APT42 IOCs", "expertise": "cti"},               │
│      {"query": "APT42 campaigns", "expertise": "general"}]      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. Create Subagents (parallel)                                 │
│     - CtiAgentRunner (mode=hybrid, priority_sources: cloud...)  │
│     - GeneralAgentRunner (mode=hybrid)                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. Run Research Loop (each agent)                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ INTERNET PHASE:                                           │   │
│  │  a. Search priority sources (site:cloud.google.com ...)   │   │
│  │  b. LLM generates search queries → Serper API             │   │
│  │  c. LLM selects URLs → Jina AI → BrowseManager (locks)    │   │
│  │  d. Summarize with citations                              │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ INTERNAL PHASE:                                           │   │
│  │  a. LLM generates query → Qdrant API (/query)             │   │
│  │  b. Group results by file_hash, calculate avg score       │   │
│  │  c. Strategy selection:                                   │   │
│  │     - avg > 0.5 → Full docs (top 3)                       │   │
│  │     - avg ≤ 0.5 → Surrounding chunks (1 per file)         │   │
│  │  d. Retrieve via InternalBrowseManager (locks)            │   │
│  │  e. Summarize with file name citations                    │   │
│  │  f. Exit when: no more unique files OR source_limit hit   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. Merge Results                                               │
│     - Collect summaries from all agents                         │
│     - Final LLM pass to create unified report                   │
│     - Deduplicate citations, format references                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Response                                     │
│  {"answer": "### Final Report\n\nIOCs Found:\n- ... [1][2]..."} │
└─────────────────────────────────────────────────────────────────┘
```

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

See [Qdrant README](./qdrant_cron/README.md)


## Challenges to tackle

- Right now, the child class doesn't do much other than provide sources to prioritize. Looking to find more use of this structure in the future.
- The intermediate summarization approach for dealing with megapages (very long webpages) is good for extracting pinpoint information (e.g. Listing IOCs of an APT). For long-form research, the intermediate summarization agent has been instructed to include specific quotes word-for-word if it is relevant to the query, but how well it works is not tested yet.
- Currently not providing google search geographic region as an option to the agent
- Currently only caching content, but the same lock and cache can be used for storing the summary as well. This saves even more calls
- Current browse retry logic retries up to 3 times no matter what the error code is. This doesn't make sense for 402 (Payment Required) for example.
- Jina started returning 402 payment required for many websites in one of my runs but when manually browsing to that URL it is publicly accessible. Checking rate limit of Jina API key with "curl https://r.jina.ai -H "Authorization: Bearer <API_KEY>" showed negative balance, further proving it is indeed Jina's rate limit
- 

## TODO

- Reduce reliance on Jina: Build custom scraper using httpx
1. Scrape using httpx
2. Check if content contains any word in the query to detect dynamic JS pages
3. If word contained, assume scrape was successful. If not, scrape using Playwright.
4. Pass raw HTML to python-readability -> trafilatura
5. Pass that into summarize function

- Further improve budgeting logic by making room for reasoning tokens, developer must specify via config file if it is reasoning