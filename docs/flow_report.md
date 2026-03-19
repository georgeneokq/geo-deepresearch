# Geo DeepResearch Flow Overview

## Complete Research Flow

When a research request is submitted, the system processes it through a pipeline of stages. The API layer receives the request and validates the query string and research mode. The query is then decomposed into specialized subqueries by an LLM, with each subquery tagged with an expertise category. For each subquery, a specialized agent is created and executed in parallel with other agents. Finally, all agent summaries are merged into a unified report with deduplicated and re-indexed citations.

A simple query with one agent typically completes in 30 to 45 seconds. Medium complexity queries with two to three agents take one to two minutes. Complex queries spawning four or more agents may require two to five minutes.

## Query Decomposition Flow

The query decomposition module receives the user's research query and uses an LLM to break it into manageable subqueries. The LLM is instructed with a system prompt that defines the available expertise categories and the expected output format. The response is parsed into a structured object containing the list of subqueries with their assigned expertise tags.

For example, a query about APT42 cyber incidents and their financial impact would be decomposed into separate subqueries for IOCs and attack techniques, malware and backdoors used, financial losses from attacks, and recent campaigns and targets. Each subquery is then routed to the appropriate specialist agent based on its expertise tag.

## Internet Research Flow

Each agent executes an iterative internet research loop when operating in internet or hybrid mode. The loop begins by checking if there are priority sources configured for the agent's domain. If priority sources exist, the agent performs deterministic searches using the site operator before moving to LLM-generated queries.

The web search phase uses the Serper API to query Google Search. The agent either uses a pre-configured priority source query or asks the LLM to generate a search query based on the research topic and previously used queries. Search results are returned as JSON containing organic results, related searches, and people also ask sections.

The webpage browsing phase selects promising URLs from search results and retrieves their content via Jina AI. Before browsing, the agent checks the cache to avoid duplicate work. If the content is not cached, the agent acquires a lock for that URL, performs the retrieval, stores the result in cache, and releases the lock. The retrieved content is then summarized to extract information relevant to the research topic.

The summarization phase updates the running summary with newly extracted information. The LLM is instructed to stay grounded in the source material, add proper citations, and deduplicate information. The loop continues until the source limit is reached or the summary approaches the token budget constraint.

## Internal Research Flow

When operating in internal or hybrid mode, agents query the internal document repository stored in Qdrant vector database. The research loop begins with an LLM generating a search query based on the research topic and previously used queries. The query is sent to the Qdrant API which performs hybrid search combining dense vector similarity and sparse vector keyword matching.

Search results are grouped by file hash to identify unique documents. For each file, the system calculates the total score by summing individual chunk scores, computes the average score, and tracks all point IDs with their scores. This grouping allows the system to make informed decisions about which files to retrieve.

The retrieval strategy depends on confidence scores. Files with an average score above 0.4 and at least two high-scoring chunks are considered high confidence. For high confidence files, the system retrieves the full document using the first point ID. For lower confidence files, the system retrieves only surrounding context chunks for the highest-scoring point in each file. This approach balances comprehensiveness with efficiency.

Retrieved documents are cached to prevent duplicate retrievals when multiple agents run in parallel. The content is summarized with file name tracking for proper citation formatting. The loop continues until the source limit is reached, no more unique files are available, or the summary exceeds the token budget.

## Chunking and Summarization Flow

Large documents exceeding token count of half the model's max context window are processed using semantic chunking. The document is split into chunks of approximately 3 fourths of the model's max context window with 10% overlap between consecutive chunks. The text splitter prioritizes structural boundaries like headings and paragraph breaks to maintain semantic coherence.

Each chunk is summarized independently with a fixed token budget calculated based on the model's capacity. The intermediate summaries are concatenated with section separators and passed through a final summarization pass to produce a cohesive summary. Documents below the chunking threshold are summarized directly in a single pass.

Token budgeting is dynamic and depends on the research round. In the first round, the system allocates 75% of the remaining token count for summarization. In subsequent rounds, the budget is calculated as the available space minus a 200-word buffer, with a minimum of 150 tokens reserved. This ensures the summary never exceeds the model's context window.

## Concurrency Control Flow

When multiple agents run in parallel, the system prevents duplicate work through caching and locking mechanisms. Before browsing a webpage or retrieving a document, an agent checks the cache. If the content is not cached, the agent acquires a lock for that specific resource.

The system supports two locking modes configured via the PARALLEL_MODE environment variable. In sequential mode, a single global master lock ensures only one agent browses at a time. This is the default mode and prevents rate limit issues on external APIs. In parallel mode, per-resource locks allow multiple agents to browse different URLs or retrieve different documents simultaneously while preventing duplicate work on the same resource.

Cache invalidation is time-based with a 60-second timeout. When an agent requests cached content, the system checks if the cached item has expired. If the cache is still valid, the content is returned immediately. If expired, the cache is cleared and the agent must re-browse the resource. This ensures reasonably fresh content while avoiding unnecessary re-fetching.

Retry logic with exponential backoff handles transient failures. When lock acquisition or API calls fail, the system retries up to three times with increasing delays. The delay is calculated as the base delay multiplied by two raised to the attempt number, plus random jitter to prevent thundering herd problems.

## Final Report Merging Flow

After all agents complete their research, the final summarization module merges the individual summaries into a unified report. If only one agent was spawned, its summary is returned directly. If multiple agents produced summaries, they are merged iteratively.

The merging process starts with the first agent's summary as the initial main report. Each subsequent summary is merged into the main report through an LLM call. The LLM is instructed to combine the information, re-index all citations for continuous numbering, and deduplicate references. The process repeats until all summaries are incorporated.

Citation re-indexing ensures the final report has a single continuous reference list. Citations from the first agent retain their original numbers. Citations from subsequent agents are renumbered to continue from the previous maximum. For example, if the first report uses citations 1 and 2, the second report's citations 1 and 2 become 3 and 4 in the merged output.

Error handling during merging allows the process to continue even if individual merge operations fail. Each merge attempt is retried up to three times with exponential backoff. If all retries fail, the problematic summary is skipped and the process continues with the next one. This graceful degradation ensures partial results are still delivered rather than complete failure.

## Temporal Awareness Flow

All LLM calls automatically append the current datetime to the system prompt for temporal awareness. This ensures that the model has explicit context about when the research is being conducted, which is critical for time-sensitive queries and for distinguishing between historical and current information.

The datetime appending is handled by the `append_current_datetime` utility function from `geo_deepresearch.tools.time`, which is called in the `call_llm` function before constructing the messages array. The datetime string is appended to the end of the system prompt, maintaining the original instruction while adding temporal context.

This pattern is applied consistently across all LLM invocations, including query decomposition, agent research loops, tool calling, and final report summarization.

## State Transitions

Each agent progresses through a defined state machine during research. The initial state has an empty summary and no sources. When research starts, the agent enters the internet research phase if configured for internet or hybrid mode. After completing internet research, agents in hybrid or internal mode transition to the internal research phase. Finally, the agent formats any errors, saves the report to a file, and returns the summary.

The token budget state tracks remaining tokens throughout the research process. Starting with the model's full context window, each summarization consumes tokens from the budget. The system calculates available space before each summary operation and adjusts the summary length accordingly. When the budget approaches exhaustion, the research loop terminates to prevent overflow.
