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

## Internal Document Processing

Internal documents are stored in Qdrant vector database with both dense and sparse vector embeddings. When an agent queries the internal repository, the system performs hybrid search combining semantic similarity and keyword matching. Results are grouped by file hash to identify unique documents, with scores aggregated to determine file-level relevance.

Only the top 3 scored chunks will be processed each time, and the retrieval strategy depends on confidence scores. Files with at least 2 chunks having a high score trigger full document retrieval. Otherwise, only surrounding context chunks are retrieved. This approach balances comprehensiveness with efficiency.

## Citation Management

The system maintains consistent citation formatting across all sources. Internal documents use the format "Internal docs - filename.pdf" in the reference list. Web sources include the full URL. All citations are numbered sequentially in the order they appear.

During final report merging, citations from all agent reports are collected, deduplicated, and re-indexed to maintain continuous numbering. Each factual statement in the report is linked to its source citation.

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
| PARALLEL_MODE | Enable concurrent execution | false |
| RESEARCH_MODE | Default research mode | hybrid |

## Performance Characteristics

Execution time varies based on query complexity and the number of agents spawned. Simple queries with a single agent typically complete in 30 to 45 seconds. Medium complexity queries with 2 to 3 agents take 1 to 2 minutes. Complex queries spawning 4 or more agents may require 2 to 5 minutes.

| Scenario | Agents | Sources | Time |
|----------|--------|---------|------|
| Simple query | 1 | 5 | 30-45 seconds |
| Medium query | 2-3 | 10-15 | 1-2 minutes |
| Complex query | 4+ | 20+ | 2-5 minutes |

The primary bottlenecks are LLM inference latency for tool calls, external API rate limits, and sequential processing of large documents through the chunking pipeline.

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

## Design Patterns

The architecture employs several design patterns to achieve flexibility and maintainability. The Strategy pattern enables different research modes through conditional execution paths. The Factory pattern creates appropriate agent instances based on expertise categories. The Singleton pattern ensures shared manager instances across all agents. The Template Method pattern defines the research loop structure with customizable steps. The Context Manager pattern handles lock acquisition and release with proper cleanup.
