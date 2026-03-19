# Geo DeepResearch Architecture

This document contains a high-level report of the architecture. More technical details and diagrams will be updated in architecture.md.

## System Overview

Geo DeepResearch is a multi-agent deep research system that automatically decomposes complex queries into specialized subtasks, each handled by domain-expert subagents. The system conducts parallel research across internet sources and internal document repositories, then merges results into a unified, citation-backed report.

The system supports three research modes: Internet mode for web-based research, Internal mode for querying internal document databases, and Hybrid mode that combines both sources for comprehensive coverage.

## Architecture Layers

### API Layer

The API layer is built with FastAPI and handles all incoming research requests. It validates the request parameters, manages the application lifecycle, and orchestrates the complete research pipeline from query decomposition through final report generation.

The main endpoint accepts a POST request with a query string and research mode, then returns a JSON response containing the final research report with citations.

### Orchestration Layer

The orchestration layer coordinates the research pipeline components. The query decomposition module uses an LLM to break complex queries into specialized subqueries and tags each with an expertise category. The agent factory maps these categories to specific agent classes and creates configured instances. The final summarization module merges multiple agent summaries into a unified report, handling citation deduplication and re-indexing.

### Agent Execution Layer

The AgentRunner base class provides common functionality for all research agents, including token budgeting, retry logic with exponential backoff, tool calling capabilities, and document chunking and summarization. Specialized agents extend this base class to add domain-specific behavior, such as priority source selection for cyber threat intelligence research.

### Manager Layer

The manager layer prevents duplicate work when multiple agents run in parallel. Three manager classes handle concurrency control: BrowseManager for webpage caching and locking, WebSearchManager for search coordination, and InternalBrowseManager for internal document retrieval. Each manager supports both sequential and parallel execution modes through configurable locking strategies.

### External Services

The system integrates with four external services. Serper API provides Google Search capabilities for web research. Jina AI handles webpage content extraction and scraping. Qdrant serves as the vector database for internal document storage and retrieval. OpenAI-compatible LLM endpoints provide all language model inference with tool calling support.

## Research Modes

The system supports three distinct research modes that determine which sources are consulted during research.

| Mode | Description | Best For |
|------|-------------|----------|
| Internet | Web search and webpage browsing only | Current events, public information, general research |
| Internal | Qdrant document search and retrieval only | Internal knowledge bases, proprietary documents |
| Hybrid | Both internet and internal research in sequence | Comprehensive research requiring multiple source types |

In Hybrid mode, the system executes internet research first, then follows with internal research, combining findings from both sources into a single report.

## Query Decomposition

When a research query is received, the system uses an LLM to decompose it into specialized subqueries. Each subquery is tagged with an expertise category that determines which agent type will handle it. The supported categories are cyber threat intelligence for security-related queries, finance for market and economic data, and general as a fallback for uncategorized topics.

For example, a query about APT42 cyber incidents and their financial impact would be decomposed into separate subqueries for IOCs and attack techniques, malware and backdoors used, financial losses from attacks, and recent campaigns and targets. Each subquery is then routed to the appropriate specialist agent.

## Agent Research Process

Each agent executes an iterative research loop that continues until reaching a minimum source count or token budget constraint. The loop consists of three phases. The search phase generates queries and retrieves results from either web search engines or the internal vector database. The browse phase selects and retrieves full content from promising sources, which is determined using the URL and the "preview" text snippet returned by Serper. The summarization phase extracts information relevant to the research topic and updates the running summary with proper citations.

Agents track used queries to avoid repetition and maintain a list of sources consulted. The research terminates when the configured source limit is reached, the summary approaches the token limit, or no more unique sources are available.

## Concurrency Control

When multiple agents run in parallel, the system prevents duplicate work through caching and locking mechanisms. Before browsing a webpage or retrieving a document, an agent checks the cache. If the content is not cached, the agent acquires a lock for that specific resource, performs the retrieval, stores the result in cache, and releases the lock.

The system supports two locking modes. Sequential mode uses a single global lock, allowing only one agent to browse at a time. Parallel mode uses per-resource locks, allowing multiple agents to browse different resources simultaneously while preventing duplicate work on the same resource.

## Token Management

The system uses dynamic token budgeting to prevent context overflow during research. Token counting is performed using the model's tokenizer loaded at application startup. The budget calculation differs between the first research round and subsequent rounds, as the first round is virtually free to use all available context due to having no prior research contents taking up the context window.

| Round | Budget Calculation |
|-------|-------------------|
| First round | 75% of remaining token count |
| Subsequent rounds | Available space minus 200 word buffer, minimum 150 tokens |

The summary is limited to 80% of the model's maximum token capacity to allow room for final processing. Token-to-word conversion uses a factor of 1.3 tokens per word for estimation purposes.

## Document Chunking

Large documents exceeding half of the model's context window are processed using semantic chunking. The document is split into chunks of approximately 3 fourths of the model's context window with 10% overlap between consecutive chunks to minimize context loss. The splitter prioritizes structural boundaries like headings and paragraph breaks to maintain semantic coherence.

Each chunk is summarized independently with a fixed token budget. The intermediate summaries are then concatenated and passed through a final summarization pass to produce a cohesive summary. Documents below the threshold are summarized directly without chunking.

# Internal Document Processing

## Document Ingestion Pipeline

Internal documents are ingested through a dedicated cron job container that continuously monitors a watch directory for new files. The ingestion process is handled by `qdrant_cron/src/main.py` and involves several sophisticated steps to ensure optimal search and retrieval quality.

### Ingestion Workflow

The ingestion workflow begins with directory watching, where the cron job runs in an infinite loop and polls the watch directory every 5 seconds for new files. It maintains an in-memory cache of already-ingested files, keyed by filename and SHA256 hash, to prevent duplicate processing.

The system accepts documents in multiple formats, including PDF, DOCX, and plain text. File conversion to markdown is handled by an external Docling service via HTTP API, which supports OCR for scanned documents and preserves structural elements such as tables and headings.

Document chunking employs a two-stage hierarchical splitting strategy. In the first stage, Langchain's `ExperimentalMarkdownSyntaxTextSplitter` splits the document at heading boundaries (H1, H2, H3) to preserve semantic sections. In the second stage, each section is further split using `RecursiveCharacterTextSplitter` with a chunk size of 700 characters and 10% overlap (70 characters). This splitter prioritizes structural boundaries like paragraph breaks, table rows, and lines to maintain coherence. Each chunk retains its absolute character index position within the original document for later context retrieval.

When enabled via the `ENABLE_DYNAMIC_CHUNK_LABELLING` environment variable, each chunk receives an intelligent, context-aware label generated by an LLM. The labeller receives the chunk text, surrounding context (500 characters before and after), document title, and previous chunk labels as input. Previous labels are provided in sequence from earliest to latest to allow the LLM to detect whether the current chunk is a continuation of a previous topic or introduces new content. This contextual labelling prevents fragmented labels like "Table 1", "Table 2" and instead produces semantically meaningful labels like "APT42 IOCs". Labels are generated sequentially to avoid LLM rate limits, although parallelism is configurable but disabled by default. If labelling fails or returns empty content, the document title is used as a fallback label.

Each chunk is embedded using both dense and sparse vectors for hybrid search. The dense vector provides semantic embeddings using `BAAI/bge-large-en-v1.5` with 1024 dimensions for semantic similarity search, while the sparse vector provides BM25 keyword-based embeddings using `Qdrant/bm25` for exact keyword matching. The embedded text is labelled by prepending the chunk label as markdown in the format `**{label}**\n\n{chunk_text}`, which boosts search accuracy by weighting important contextual keywords from the label. Both vectors are stored in Qdrant under separate configurations.

Each chunk receives a deterministic UUID v5 generated from the file SHA256 hash and chunk index in the format `{hash}_{index}`. This ensures the same chunk always maps to the same point ID, enabling idempotent upserts.

Each Qdrant point stores rich metadata in its payload, including the original document filename (`file_name`), the SHA256 hash of the original file (`file_hash`), the sequential index of the chunk within the document for reordering purposes when retrieving chunks from the same document (`chunk_index`), the character position of the chunk in the original document (`substring_index`), the dynamic or static label for the chunk (`label`), and the raw chunk text without the label prefix (`text`).

After successful ingestion, a JSON file containing the extracted markdown text and file hash is stored in the processed documents directory. This cache is used for retrieving full document text and surrounding context without re-processing.

### Qdrant Collection Setup

On startup, the cron job initializes the Qdrant collection if it does not exist. The collection is configured with a dense vector configuration using cosine distance, a sparse vector index stored on-disk for memory efficiency, and a payload index on the `file_name` field for fast file-based lookups.

## Retrieval API Layer

The Qdrant Retriever API provides a FastAPI-based interface for querying and retrieving documents from the vector database.

### API Endpoints

The API exposes four endpoints. The `/health` endpoint responds to GET requests with a health check returning `{"status": "healthy"}`. The `/query` endpoint responds to GET requests and searches for similar documents using hybrid search. The `/documents/{point_id}` endpoint responds to GET requests and retrieves the full text of a document by point ID. The `/documents/{point_id}/surrounding` endpoint responds to GET requests and retrieves a chunk by point ID with configurable surrounding context length.

### Query Endpoint

The `/query` endpoint performs hybrid search combining dense and sparse vectors. It accepts a query string, a result limit ranging from 1 to 50 with a default of 5, and an optional collection name. The endpoint executes two parallel prefetch queries: dense semantic search with a limit of 20 results and sparse keyword search with a limit of 20 results. Results are fused using Reciprocal Rank Fusion (RRF) to combine rankings from both search methods. The endpoint returns the top-k results with point ID, similarity score, and full payload.

### Surrounding Context Retrieval

The `/documents/{point_id}/surrounding` endpoint provides dynamic context window retrieval. It retrieves the chunk at the specified point ID plus surrounding text before and after. The `max_chars` query parameter controls how many characters to include on each side, with a default of 500 and a valid range of 100 to 10000. The total context size equals `max_chars` before the chunk plus the chunk text plus `max_chars` after the chunk. The recommended value of 500 characters on each side, approximately 100 to 150 words, provides sufficient context for most use cases while keeping response sizes manageable. Context is extracted using the stored `substring_index` from the processed document cache. This allows callers to adjust context based on their needs, using smaller values for focused snippets and larger values for comprehensive understanding, although it is currently hard coded to a larger value to prevent losing context.

### Full Document Retrieval

The `/documents/{point_id}` endpoint returns the complete extracted text of a document. It uses the `file_name` from the point's payload to locate the processed document cache and returns the full markdown-converted text content. This endpoint is useful when analysis requires the complete document rather than just chunks.

## Search and Retrieval Strategy

When agents query the internal repository during research, they employ a multi-stage retrieval strategy. Queries use hybrid search combining both semantic similarity through dense vectors and keyword matching through sparse vectors, fused via Reciprocal Rank Fusion. Results are grouped by `file_hash` to identify unique documents, with scores aggregated at the file level.

The system employs adaptive retrieval based on confidence scores. Files with two or more high-scoring chunks trigger full document retrieval, while otherwise only the top 3 scored chunks with surrounding context are retrieved. Retrieved chunks can be expanded with surrounding text via the API to provide better context for summarization.

This architecture balances comprehensiveness with efficiency, ensuring agents have access to relevant context without overwhelming the token budget.

## Citation Management

The system maintains consistent citation formatting across all sources. Internal documents use the format "Internal docs - filename.pdf" in the reference list, while web sources include the full URL. All citations are numbered sequentially in the order they appear.

During final report merging, citations from all agent reports are collected, deduplicated, and re-indexed to maintain continuous numbering. Each factual statement in the report is linked to its source citation.

## Observability and Tracing

The system was built with observability in mind. Environment variables can be configured to point to a Langfuse instance, which acts as the OpenTelemetry backend that receives traces. While many telemetry backends exist, Langfuse is built specifically for AI applications, providing an SDK that serves as a drop-in replacement for the standard OpenAI library.

LLM calls are traced from the start of each call to the deep research API server and are stored in a tree format. In each node, developers can check how much each LLM call costs, which is useful for cloud LLM calls, as well as time taken, inputs, and outputs. This tracing capability was essential in debugging issues and identifying bottlenecks in the system.

## Configuration

The system is configured through environment variables that control API endpoints, model selection, and operational parameters.

| Variable | Purpose | Default Value |
|----------|---------|---------------|
| DEEP_RESEARCH_API_KEY | LLM API authentication | Required |
| DEEP_RESEARCH_BASE_URL | LLM API endpoint | Required |
| DEEP_RESEARCH_MODEL | Model name for inference | z-ai/glm-4.7-flash |
| DEEP_RESEARCH_MODEL_MAX_TOKENS | Context window size | 100000 |
| JINA_API_KEY | Web scraping API key | Required |
| SERPER_API_KEY | Google Search API key | Required |
| QDRANT_API_URL | Vector database endpoint | http://qdrant_api_server:8000 |
| QDRANT_URL | Qdrant connection URL for cron job | http://qdrant:6333 |
| QDRANT_COLLECTION_NAME | Qdrant collection name | internal_docs |
| INGEST_DIR | Directory watched for new documents | /app/ingest_docs |
| PROCESSED_DIR | Directory for processed document cache | /app/processed_docs |
| DOCLING_BASE_URL | Docling conversion service URL | http://docling-serve:5001 |
| ENABLE_DYNAMIC_CHUNK_LABELLING | Enable LLM-based chunk labelling | false |
| CHUNK_LABELLER_MODEL_API_KEY | API key for chunk labeller LLM | Required (if enabled) |
| CHUNK_LABELLER_MODEL_BASE_URL | Base URL for chunk labeller LLM | Required (if enabled) |
| CHUNK_LABELLER_MODEL | Model name for chunk labelling | qwen/qwen3.5-9b |
| DENSE_EMBEDDING_MODEL | Dense vector embedding model | sentence-transformers/all-MiniLM-L6-v2 |
| DENSE_EMBEDDING_SIZE | Dense vector dimension | 384 |
| SPARSE_EMBEDDING_MODEL | Sparse vector embedding model | Qdrant/bm25 |
| PARALLEL_MODE | Enable concurrent execution | false |
| RESEARCH_MODE | Default research mode | hybrid |
| LANGFUSE_SECRET_KEY | Langfuse authentication secret | Optional |
| LANGFUSE_PUBLIC_KEY | Langfuse authentication public | Optional |
| LANGFUSE_BASE_URL | Langfuse endpoint URL | Optional |

## Performance Characteristics

Execution time varies based on several factors, including cloud or self-hosted machine GPU processing speed, especially for content summarization, whether parallel mode is enabled, and external API rate limits from services such as Serper and Jina, which increase execution time due to retrying with exponential backoff and jitter.

While many parts of the application could be parallelized and made to execute very quickly, parallelization has been disabled during testing due to issues with Jina rate limits and self-hosted model processing limits. The primary bottlenecks are external API rate limits, sequential processing of large documents through the chunking pipeline, and model reasoning if enabled.

## Error Handling

The system implements retry logic with exponential backoff for transient failures. LLM rate limit errors trigger automatic retries with increasing delays. API failures are logged and handled gracefully, with the research continuing using available sources. Lock acquisition timeouts prevent deadlocks by releasing locks after 60 seconds.

When individual sources fail to load after multiple retry attempts, they are skipped and the research continues with remaining sources. If all agents fail, the system returns an error message rather than an empty report.

## Temporal Awareness

All LLM calls automatically append the current datetime to the system prompt for temporal awareness. This ensures that the model has explicit context about when the research is being conducted, which is critical for time-sensitive queries and for distinguishing between historical and current information.

The datetime appending is handled by the `append_current_datetime` utility function from `geo_deepresearch.tools.time`, which is called in the `call_llm` function before constructing the messages array. The datetime string is appended to the end of the system prompt, maintaining the original instruction while adding temporal context.

This pattern is applied consistently across all LLM invocations, including query decomposition, agent research loops, tool calling, and final report summarization.

## Directory Structure

The codebase follows a modular structure with clear separation of concerns.

| Directory/File | Purpose |
|----------------|---------|
| main.py | FastAPI application entrypoint |
| decompose.py | Query decomposition logic |
| summarize.py | Final report merging |
| tokenize.py | Token counting utilities |
| subagents/ | Agent classes and factory |
| browse_manager.py | Webpage caching and locking |
| internal_browse_manager.py | Document caching and locking |
| util/ | Shared utilities for LLM, logging, tools |
| qdrant_cron/src/main.py | Document ingestion cron job entrypoint |
| qdrant_cron/src/embedding.py | Text chunking and embedding utilities |
| qdrant_cron/src/extract.py | Document conversion (PDF, DOCX to markdown) |
| qdrant_cron/src/label.py | Dynamic chunk labelling with LLM |
| qdrant_cron/src/retrieval.py | Query and context retrieval logic |
| qdrant_cron/src/server/api_server.py | Qdrant retrieval FastAPI server |
| qdrant_cron/src/constants.py | Configuration constants for Qdrant service |
| qdrant_cron/src/schemas.py | Type definitions (Chunk, etc.) |

## Design Patterns

The architecture employs several design patterns to achieve flexibility and maintainability. The Strategy pattern enables different research modes through conditional execution paths. The Factory pattern creates appropriate agent instances based on expertise categories. The Singleton pattern ensures shared manager instances across all agents. The Template Method pattern defines the research loop structure with customizable steps. The Context Manager pattern handles lock acquisition and release with proper cleanup.
