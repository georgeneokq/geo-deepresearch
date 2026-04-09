from enum import Enum
from typing import Any
import traceback
import abc
import asyncio
import time
import json
import logging
import os
import httpx
import random
from collections import deque
from pathlib import Path
from typing import Optional, Any, Dict
from openai import AsyncOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from geo_deepresearch.tokenize import count_tokens
from geo_deepresearch.util.tools import function_to_schema
from geo_deepresearch.config import config
from geo_deepresearch.util.logging import get_logger
from geo_deepresearch.util.llm import call_llm, openai_default_client, openai_default_model
from geo_deepresearch.constants import MODEL_MAX_TOKENS
from geo_deepresearch.browse_manager import (
    BrowseManager,
    browse_manager as browse_manager_instance,
)
from geo_deepresearch.web_search_manager import (
    WebSearchManager,
    web_search_manager as web_search_manager_instance,
)
from geo_deepresearch.internal_browse_manager import (
    InternalBrowseManager,
    internal_browse_manager as internal_browse_manager_instance,
)

logger = get_logger()


class ResearchMode(Enum):
    INTERNET = "internet"
    INTERNAL = "internal"
    HYBRID = "hybrid"

# Grounding instruction to prevent hallucination
GROUNDING_INSTRUCTION = """
IMPORTANT: You must be completely grounded in the provided source material.
- Do NOT add any information that is not explicitly present in the provided sources.
- Do NOT make assumptions, inferences, or connections that are not directly stated in the sources.
- Do NOT use any external knowledge or training data to supplement the provided information.
- If the sources do not contain information about a topic, explicitly state that the information is not available in the provided sources.
- Do NOT associate entities, names, or aliases that are not explicitly mentioned in the sources (e.g., do not add alternative APT group names like "Cozy Bear" unless the source explicitly states the equivalence).
- Every factual statement must be supported by a citation from the provided sources.
- When summarizing, only extract what is directly stated - do not elaborate beyond what the sources contain.
""".strip()

WEB_SEARCH_INSTRUCTIONS = f"""
Given web search tool, perform web search to find information on the given research topic.
As it uses Google search under the hood, you may use advanced operators like "site:", "intitle", etc. where necessary.
The user will provide a list of used queries, avoid repeating same queries, at least paraphrase. (e.g. \"IOCs\" can be paraphrased to \"Domains\", \"URLs\")
Keep your query short to return relevant search results from Google.

{GROUNDING_INSTRUCTION}
""".strip()

WEBPAGE_BROWSE_INSTRUCTIONS = f"""
Given a research topic and web search results from previous agent, rank the top 3 webpages with relevance to the research topic, then browse them.
The user may provide a list of existing citations, avoid browsing those websites.

{GROUNDING_INSTRUCTION}
""".strip()

INTERNAL_SEARCH_INSTRUCTIONS = f"""
Given a research topic, query the internal document store (Qdrant) to find relevant documents.
The user will provide a list of used queries, avoid repeating same queries, at least paraphrase. (e.g. \"IOCs\" can be paraphrased to \"Domains\", \"URLs\")

{GROUNDING_INSTRUCTION}
""".strip()

INTERNAL_BROWSE_INSTRUCTIONS = f"""
Given a research topic and internal document search results, select the top 3 most relevant documents to retrieve and summarize.
Avoid documents that have already been cited.

{GROUNDING_INSTRUCTION}
""".strip()

REPORT_AGENT_INSTRUCTIONS = f"""
You are a report writer agent.
You will be given a research topic, along with the report so far.
Given the web search and webpage browsing tool results, add to the existing citation list and report using information from the previous tool results.
You should only extract out information relevant to the research topic for updating the report.
When reading the tool results, note that they are summaries and may include notes on truncated data.
As a report writer, you should exclude such information.
Deduplicate or merge information as necessary, but ensure that every source, even if not referenced, is included in the citation list.
Write your report in well structured markdown, suitable for conversion into a Word document.
Ensure to include a title for the report.
All statements in your answer must be linked to a citation.
Ensure to keep all previously linked citations and references list.

Use the following citation format:
- In-text citation: [1], [2], etc.
- Internal document citations (items with UUID as key): "1. Internal docs - <file name>.pdf"
- Website citations (items with URL as key): "2. <full URL>"

---

Example 1 - Web source:
{{
    "http://cloud.google.com": "Webpage summary here..."
}}

References:
1. https://cloud.google.com

---

Example 2 - Internal docs:
{{
    "e91604e9-6ab0-51be-8f59-6fd2fe6903f5": {{
        "file_name": "The history of APT33",
        "summary": "Document summary here..."
    }}
}}

References:
1. https://cloud.google.com
2. Internal docs - The history of APT33

---

{GROUNDING_INSTRUCTION}

---

Refer to example response below, but be more detailed where necessary.

--- Start of example ---
IOCs found:
- www.badsite.com [1]
- 162.108.0.2 [2]
- APT42 uses NICECURL backdoor [3]

References:
1. https://cloud.google.com
2. https://www.citation2.com
3. Internal docs - APT42's recent activity.pdf
--- End of example ---
""".strip()


class AgentRunner(abc.ABC):
    browse_manager: BrowseManager
    web_search_manager: WebSearchManager
    internal_browse_manager: InternalBrowseManager
    source_list: list[str]
    failed_browses: list[str]
    used_web_search_queries: list[str]
    used_internal_search_queries: list[str]
    num_rounds: int
    research_topic: str
    summary: str
    jina_api_key: str
    jina_timeout: float
    remaining_token_count: int
    available_tools: dict
    tools_schema: list
    mode: ResearchMode
    qdrant_api_url: str
    internal_sources: list[str]

    @abc.abstractmethod
    def priority_sources(self) -> dict[str, str]:
        """
        Return a dictionary of description to URL.
        The keys are currently not used, but possible usage is anticipated in the future.
        Put a concise description as the key.
        The value should be the base URL to prioritize. This will be used in an advanced query operator "site:".
        Example dict: {"IOCs": "cloud.google.com"}
        Example query to Google:
        ```
        site:cloud.google.com IOCs of APT33
        ```

        Returns:
            dict[str, str]: Mapping of description to URL
        """
        pass

    @abc.abstractmethod
    def source_limit(self) -> int:
        """
        Return an integer that controls the number of sources to hit.
        Once the specified number is hit, the current deep research session will end with the current round.
        This is not a hard cap as multiple webpages may be taken into consideration during each round.
        A value of 5 is recommended, and is the default value.
        You may want to increase the limit for more complex topics that may require more browsing.
        """
        return 5

    def __init__(
        self,
        openai_base_url: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        model: Optional[str] = None,
        browse_manager: Optional[BrowseManager] = browse_manager_instance,
        web_search_manager: Optional[WebSearchManager] = web_search_manager_instance,
        internal_browse_manager: Optional[InternalBrowseManager] = internal_browse_manager_instance,
        mode: Optional[ResearchMode] = None,
        qdrant_api_url: Optional[str] = None,
    ):
        """
        Base class for creating specialized subagent for deep research in a specific field.
        Provides implementations for common behaviours like summarizing and chunking strategy.

        Args:
            openai_base_url (str):  OpenAI-compatible base URL for the deep research agent.
                                    Leave blank to pull from environment variable `DEEP_RESEARCH_BASE_URL`
            openai_api_key (str):   OpenAI-compatible API key for the deep research agent.
                                    Leave blank to pull from environment variable `DEEP_RESEARCH_API_KEY`
            model (str):            Model name of the deep research agent.
                                    Leave blank to pull from environment variable `DEEP_RESEARCH_MODEL`.
            mode (ResearchMode):    Research mode: INTERNET, INTERNAL, or HYBRID.
                                    Defaults to HYBRID if not specified.
            qdrant_api_url (str):   URL for the Qdrant API server.
                                    Leave blank to pull from environment variable `QDRANT_API_URL`.
        """

        self.client = AsyncOpenAI(
            base_url=(openai_api_key or os.environ.get("DEEP_RESEARCH_BASE_URL")),
            api_key=(openai_base_url or os.environ.get("DEEP_RESEARCH_API_KEY")),
        )
        self.model = model or os.environ.get(
            "DEEP_RESEARCH_MODEL", "z-ai/glm-4.7-flash"
        )

        assert browse_manager
        self.browse_manager = browse_manager

        assert web_search_manager
        self.web_search_manager = web_search_manager

        assert internal_browse_manager
        self.internal_browse_manager = internal_browse_manager

        self.source_list = []
        self.failed_browses = []
        self.used_web_search_queries = []
        self.used_internal_search_queries = []
        self.num_rounds = 0
        self.research_topic = ""
        self.summary = "No research done yet"

        self.jina_api_key = os.environ.get("JINA_API_KEY", "")
        self.jina_timeout = 60.0
        self.remaining_token_count = int(
            os.environ.get("DEEP_RESEARCH_MODEL_MAX_TOKENS", 100000)
        )

        self.mode = mode or ResearchMode(os.environ.get("RESEARCH_MODE", "hybrid"))
        self.qdrant_api_url = qdrant_api_url or os.environ.get("QDRANT_API_URL", "http://qdrant_api_server:8000")
        self.internal_sources = []

        # Register tools for introspection
        self.available_tools = {
            "web_search": self.web_search,
            "webpage_browse": self.webpage_browse,
            "internal_search": self.internal_search,
            "internal_browse": self.internal_browse,
        }
        self.tools_schema = [
            function_to_schema(f) for f in self.available_tools.values()
        ]

    def _token_count_to_word_count(self, token_count: int):
        return int(token_count / 1.3)

    def _word_count_to_token_count(self, word_count: int) -> int:
        return int(word_count * 1.3)

    async def _make_serper_request(
        self, endpoint: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Makes a request to the Serper API.

        Args:
            endpoint (str): The API endpoint
            params (Dict[str, Any]): Request parameters

        Returns:
            Dict[str, Any]: Search response
        """
        try:
            serper_api_key = os.environ.get("SERPER_API_KEY")
            if not serper_api_key:
                logger.error("No Serper API key provided")
                return {"success": False, "error": "Please provide a Serper API key"}

            url = f"https://google.serper.dev/{endpoint}"
            if endpoint == "scrape":
                url = "https://scrape.serper.dev"

            headers = {"X-API-KEY": serper_api_key, "Content-Type": "application/json"}

            # Add optional parameters
            # TODO: Make use of these
            # if self.date_range:
            #     params["tbs"] = self.date_range
            # if self.location:
            #     params["gl"] = self.location

            # if self.language:
            #     params["hl"] = self.language

            logger.debug(f"Making request to {url} with params: {params}")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, headers=headers, json=params, timeout=15.0
                )
                response.raise_for_status()

                logger.debug(f"Successfully received response from {endpoint} endpoint")
                return {
                    "success": True,
                    "data": response.json(),
                    "raw_response": response.text,
                }
        except Exception as e:
            logger.error(f"Serper API error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def web_search(
        self,
        query: str,
        num_results: Optional[int] = None,
    ) -> str:
        """
        Searches Google for the provided query using the Serper API.

        Args:
            query (str): The search query to search for on Google.
            num_results (int, optional): Number of search results to retrieve.

        Returns:
            str: A JSON-formatted string containing the search results or an error message if the search fails.
        """
        try:
            if not query:
                return json.dumps(
                    {"error": "Please provide a query to search for"}, indent=2
                )

            async with self.web_search_manager.acquire_web_search_lock():
                # Cache query
                self.used_web_search_queries.append(query)

                logging.debug(f"Searching Google for: {query}")

                params = {
                    "q": query,
                    "num": num_results or 5,
                }

                result = await self._make_serper_request("search", params)

                if result["success"]:
                    logger.debug(
                        f"Successfully found Google search results for query: {query}"
                    )
                    return result["raw_response"]
                else:
                    logger.error(
                        f"Error searching Google for query {query}: {result['error']}"
                    )
                    return json.dumps({"error": result["error"]}, indent=2)

        except Exception as e:
            logger.error(f"Unexpected error searching Google for query {query}: {e}")
            return json.dumps(
                {"error": f"An unexpected error occurred: {str(e)}"}, indent=2
            )


    def _semantic_chunker(self, text: str, max_tokens: int = 7000, overlap: int = 500):
        """
        Splits text into chunks based on token count using structural boundaries.
        """
        # Use your count_token function as the length metric.
        # This makes the splitter evaluate chunk_size in terms of tokens.
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=max_tokens,
            chunk_overlap=overlap,
            length_function=count_tokens,
            separators=[
                "\n\n# ", "\n\n## ", "\n\n### ", 
                "\n\n",   # Prioritize paragraph breaks
                "\n|",    # Keep table rows together
                "\n",      # Line breaks
                ". ",      # Sentences
                " ", ""
            ],
            strip_whitespace=False,
        )

        # split_text returns a list of strings
        chunks = text_splitter.split_text(text)
        
        return chunks

    def _get_jina_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
        }
        if self.jina_api_key:
            headers["Authorization"] = f"Bearer {self.jina_api_key}"
        if self.jina_timeout:
            headers["X-Timeout"] = str(self.jina_timeout)

        return headers

    # TODO: TEST RUN
    async def webpage_browse(self, urls: list[str]):
        """
        Browse specified webpages.
        Webpage contents will be summarized to save tokens.

        Args:
            urls (list[str]): List of URLs to browse

        Returns:
            str: A JSON-formatted string containing a mapping of URL browsed to summarized contents.
        """
        # Map URL to summary
        summaries = {}

        async def process_url(url):
            if url in self.source_list:
                return "[SYSTEM NOTICE] You have already browsed this webpage."

            full_url = f"https://r.jina.ai/{url}"
            logger.debug(f"Browsing {url}...")

            # Check the cache to get webpage content.
            # If another agent is in the middle of browsing it, this function call will wait
            # until the lock is released. While the cache should be populated in the case of no failure,
            # we have to account for failures in the subsequent code.
            raw_webpage_content = await self.browse_manager.get_cached_webpage(url)

            if raw_webpage_content:
                # Log successful cache hit
                logger.debug(f"Cache hit for {url}!")
                logger.debug(f"Raw webpage content: {raw_webpage_content}")

            try:
                # Edge case handling:
                # Cache read and lock acquiring, another agent acquires the lock for this url.
                # If that agent fails to populate the cache, perhaps due to timeout,
                # raw_webpage_content will be empty after lock is released here.
                # To handle this, we do a retry loop, and give up after specified max retries to prevent deadlocks.
                max_retries = 3
                last_error: Optional[Exception] = None
                for i in range(max_retries):
                    if raw_webpage_content:
                        # If cache hit, we bypass the browsing
                        break

                    # If cache miss / previous browse failed, attempt to browse the url.
                    # Ensure to lock so that other agents don't do double work
                    logger.debug(f"Acquiring lock for {url} (attempt {i + 1}/{max_retries})")
                    try:
                        async with self.browse_manager.acquire_browse_lock(url):
                            logger.debug(f"Acquired lock for {url}")
                            async with httpx.AsyncClient() as client:
                                logger.debug(f"Making request to {full_url}...")
                                response = await client.get(
                                    full_url,
                                    headers=self._get_jina_headers(),
                                    timeout=self.jina_timeout,
                                )

                            response.raise_for_status()
                            jina_response = response.json()
                            # Jina JSON structure usually has content in 'data', 'content', or 'markdown'
                            jina_data = jina_response.get("data", jina_response)

                            raw_webpage_content = jina_data.get("content", "")
                            logger.debug(f"Successfully browsed {url}")
                            logger.debug(
                                f"Jina response:\n{json.dumps(jina_data, indent=2)}"
                            )
                            logger.debug(
                                f"Jina extracted content: {raw_webpage_content[:200]}"
                            )

                            # Add to cache
                            self.browse_manager.add_to_cache(url, raw_webpage_content)

                            # Successfully retrieved webpage contents and added to cache,
                            # break out of loop and release lock
                            break
                    except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError) as e:
                        last_error = e
                        logger.warning(f"Attempt {i + 1}/{max_retries} failed for {url}: {type(e).__name__}: {e}")
                        if i < max_retries - 1:
                            # Exponential backoff with jitter
                            base_delay = 5.0  # Base delay in seconds
                            exponential_delay = base_delay * (2 ** i)  # 1s, 2s, 4s, ...
                            jitter = random.uniform(0, exponential_delay * 0.5)  # Add up to 50% jitter
                            delay = exponential_delay + jitter
                            logger.debug(f"Retrying {url} in {delay:.2f}s...")
                            await asyncio.sleep(delay)
                        continue

                if not raw_webpage_content:
                    # Max retries hit and still failed. Give up on this source
                    error_msg = str(last_error) if last_error else "Unknown error"
                    raise RuntimeError(
                        f"Failed to browse after {max_retries} attempts: {url} - {error_msg}"
                    )

                # Use shared chunking and summarization logic
                summarized = await self.chunk_and_summarize(
                    raw_webpage_content
                )

                self.source_list.append(url)
                logger.debug(f"After adding to source list:")
                logger.debug(f"{'\n'.join([f'- {item}' for item in self.source_list])}")
                summaries[url] = summarized

            except Exception as e:
                traceback.print_exc()
                self.failed_browses.append(url)
                return f"Error reading URL: {str(e)}"

        # Process in parallel or sequence depending on the configuration
        if config.is_parallel_mode_enabled():
            await asyncio.gather(*[process_url(url) for url in urls])
        else:
            for url in urls:
                await process_url(url)

        return summaries

    async def summarize_document(
        self, contents: str, recommended_max_tokens: int
    ) -> str:
        # Max tokens is used for recommended word limit calculation, not a hard cap
        recommended_word_limit = self._token_count_to_word_count(recommended_max_tokens)

        summarizer_instructions = f"""
Given the following research topic and webpage contents, extract out only the information relevant to the query.
The webpage contents may be truncated. If it seems truncated, summarize while noting a possible lack of context due truncation.
Aim to be concise to save tokens, but do not skip information that has any relevance to the research topic.
Summarize in a way that the agent receiving your summary can understand it without extra context.
The data might be chunked; if it is, ensure to deduplicate information, as there is some chunking overlap to avoid loss of context.
For the sake of long-form open-ended responses, you should include a "Quotes" section where you write a list quotes word-for-word if they are relevant to the given query.
Estimated word count limit: {recommended_word_limit}.
Use the word count limit as a guideline on how concise you must be.
If no useful information, just say \"No information found\".

{GROUNDING_INSTRUCTION}
        """.strip()
        user_prompt = f"Query: {self.research_topic}\n\nWebpage contents:\n\n{contents}"
        res = await call_llm(
            openai_default_client, openai_default_model, summarizer_instructions, user_prompt
        )
        if not res.content:
            logger.error("Unexpected empty summarization. Response here:")
            logger.error(res)
        return res.content or ""

    async def chunk_and_summarize(
        self, contents: str
    ) -> str:
        """
        Shared chunking and summarization logic for both web and internal documents.
        
        Args:
            contents: Raw text content to process
            source_identifier: Identifier for the source (URL or file path)
            recommended_max_tokens: Recommended maximum tokens for the summary
            
        Returns:
            Summarized content
        """
        # --- START: RAG-Inspired Semantic Chunking ---
        incoming_tokens = count_tokens(contents)

        if incoming_tokens > MODEL_MAX_TOKENS / 2:
            logger.debug(
                f"Large document detected ({incoming_tokens} tokens). Processing in chunks..."
            )
            # We use overlap so the model doesn't lose context between chunks.
            # Use 3/4 if max number of tokens model can process.
            max_tokens_per_chunk = int(MODEL_MAX_TOKENS * 0.75)
            recommended_output_tokens = MODEL_MAX_TOKENS - max_tokens_per_chunk - 200
            chunks = self._semantic_chunker(
                contents, max_tokens=max_tokens_per_chunk, overlap=int(max_tokens_per_chunk * 0.1)
            )

            # Semantic chunker sometimes only returns 1 chunk, in this case don't need to do aggregation of summaries
            if len(chunks) > 1:
                intermediate_summaries = []

                # Run in parallel if PARALLEL_CHUNK_SUMMARIZATION is enabled, number of parallel slots is defined in env.
                # However if disabled, num_parallel_slots is set to 1 to force sequential processing.
                parallel_chunk_summarization = os.environ.get("PARALLEL_CHUNK_SUMMARIZATION", "").lower() == "true"
                num_parallel_slots = 1 if not parallel_chunk_summarization else int(os.environ.get("PARALLEL_SLOTS", 2))

                # Define task to be ran in parallel
                async def task(chunk: str, total_chunks: int, semaphore: asyncio.Semaphore, task_id: str | int):
                    async with semaphore:
                        try:
                            logger.debug(f"Processing chunk {task_id}/{total_chunks}...")
                            # Each chunk gets a fixed budget for its mini-summary
                            chunk_summary = await self.summarize_document(chunk, recommended_output_tokens)
                            logger.debug(f"Summary for chunk {task_id}: {chunk_summary}")
                            return chunk_summary
                        except Exception as e:
                            logger.error(f"Error in processing chunk {task_id}: {str(e)}")
                            traceback.print_exc()
                            return "Failed to process chunk."

                # Run summarization tasks
                sem = asyncio.Semaphore(num_parallel_slots)
                status = "enabled" if parallel_chunk_summarization else "disabled (sequential)"
                logger.debug(f"Parallel chunk summarization {status}. Concurrency limit: {num_parallel_slots}")
                num_chunks = len(chunks)
                intermediate_summaries = await asyncio.gather(*[task(chunk, num_chunks, sem, i+1) for i, chunk in enumerate(chunks)])

                # Consolidate: This becomes the new input for the final update
                contents = "\n\n--- NEXT SECTION ---\n\n".join(
                    intermediate_summaries
                )
        # --- END: Chunking ---

        # Budgeting Logic
        MIN_SUMMARY_ROOM = 150
        buffer_tokens = self._word_count_to_token_count(200)
        current_summary_size = count_tokens(self.summary) if self.summary else 0

        if self.num_rounds == 0:
            # 3/4 of remaining token count
            summarize_max_tokens = int(self.remaining_token_count / 4 * 3)
        else:
            available_space = (
                self.remaining_token_count
                - current_summary_size
                - buffer_tokens
            )
            summarize_max_tokens = max(available_space, MIN_SUMMARY_ROOM)

        logger.debug(
            f"Budgeting {summarize_max_tokens} tokens for summarizing:\n{contents[:200]}...\n"
        )
        summarized = await self.summarize_document(
            contents, summarize_max_tokens
        )

        return summarized

    async def _query_qdrant_api(
        self, endpoint: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Makes a request to the Qdrant API server.

        Args:
            endpoint (str): The API endpoint (e.g., "query", "documents/{id}")
            params (Dict[str, Any]): Request parameters

        Returns:
            Dict[str, Any]: API response
        """
        try:
            url = f"{self.qdrant_api_url}/{endpoint}"
            
            logger.debug(f"Making request to {url} with params: {params}")
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=30.0)
                response.raise_for_status()

                logger.debug(f"Successfully received response from Qdrant API")
                return {
                    "success": True,
                    "data": response.json(),
                    "raw_response": response.text,
                }
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Qdrant API error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def internal_search(
        self,
        query: str,
        limit: Optional[int] = None,
    ) -> str:
        """
        Searches the internal document store (Qdrant) for relevant documents.

        Args:
            query (str): The search query to search for in the internal document store.
            limit (int, optional): Number of search results to retrieve. Recommended minimum of 10.

        Returns:
            str: A JSON-formatted string containing the search results or an error message if the search fails.
        """
        try:
            if not query:
                return json.dumps(
                    {"error": "Please provide a query to search for"}, indent=2
                )

            # Cache query
            self.used_internal_search_queries.append(query)

            logging.debug(f"Searching internal documents for: {query}")

            params = {
                "query": query,
                "limit": limit or 15,  # Fetch more to allow for filtering
            }

            result = await self._query_qdrant_api("query", params)

            if result["success"]:
                logger.debug(
                    f"Successfully found internal search results for query: {query}"
                )
                return result["raw_response"]
            else:
                logger.error(
                    f"Error searching internal documents for query {query}: {result['error']}"
                )
                return json.dumps({"error": result["error"]}, indent=2)

        except Exception as e:
            logger.error(f"Unexpected error searching internal documents for query {query}: {e}")
            return json.dumps(
                {"error": f"An unexpected error occurred: {str(e)}"}, indent=2
            )

    def _group_qdrant_results_by_file(
        self, search_results: list[dict], score_threshold: float = 0.5
    ) -> list[dict]:
        """
        Groups Qdrant search results by file_hash and returns detailed file information.

        Takes each list_item["score"], groups by list_item["file_hash"] and creates 
        a mapping with detailed statistics including average score, total score, 
        and all point IDs with their individual scores.

        Args:
            search_results (list[dict]): List of Qdrant search results with id, score, and payload
            score_threshold (float): Threshold for filtering point IDs (default 0.5)

        Returns:
            list[dict]: List of file info dictionaries with structure:
                {
                    "file_hash": str,
                    "file_name": str,
                    "total_score": float,
                    "average_score": float,
                    "point_count": int,
                    "first_point_id": str,
                    "all_point_ids": list[str],
                    "high_scoring_point_ids": list[str],  # Points with score > threshold
                    "point_scores": dict[str, float]  # Mapping of point_id -> score
                }
        """
        # Map file_hash -> detailed info
        file_hash_map: Dict[str, dict] = {}

        for item in search_results:
            point_id = str(item.get("id", ""))
            score = item.get("score", 0.0)
            payload = item.get("payload", {})
            file_hash = payload.get("file_hash", "")
            file_name = payload.get("file_name", "unknown")

            if not file_hash:
                logger.warning(f"Point {point_id} missing file_hash, skipping")
                continue

            if file_hash in file_hash_map:
                # Update existing file info
                file_info = file_hash_map[file_hash]
                file_info["total_score"] += score
                file_info["point_count"] += 1
                file_info["all_point_ids"].append(point_id)
                file_info["point_scores"][point_id] = score
                if score > score_threshold:
                    file_info["high_scoring_point_ids"].append(point_id)
            else:
                # First occurrence of this file
                file_hash_map[file_hash] = {
                    "file_hash": file_hash,
                    "file_name": file_name,
                    "total_score": score,
                    "point_count": 1,
                    "first_point_id": point_id,
                    "all_point_ids": [point_id],
                    "high_scoring_point_ids": [point_id] if score > score_threshold else [],
                    "point_scores": {point_id: score}
                }

        # Calculate average scores
        for file_info in file_hash_map.values():
            file_info["average_score"] = file_info["total_score"] / file_info["point_count"]

        # Sort by total score in descending order
        sorted_files = sorted(
            file_hash_map.values(),
            key=lambda x: x["total_score"],
            reverse=True
        )

        logger.debug(f"Grouped results into {len(sorted_files)} unique files")
        logger.debug(sorted_files)
        return sorted_files

    async def internal_browse(
        self,
        point_ids: list[str],
        use_surrounding: bool = False,
        max_chars: int = 500,
        point_id_to_file_name: Optional[Dict[str, str]] = None
    ) -> tuple[str, list[str]]:
        """
        Retrieves and summarizes internal documents from Qdrant by point IDs.

        Args:
            point_ids (list[str]): List of Qdrant point IDs to retrieve
            use_surrounding (bool): If True, retrieve surrounding text chunks instead of full documents
            max_chars (int): Max surrounding characters on each side (only used if use_surrounding is True)
            point_id_to_file_name (Dict[str, str]): Optional mapping of point_id to file name for citation

        Returns:
            tuple[str, list[str]]: A tuple containing:
                - JSON-formatted string containing a mapping of point ID to summarized contents with file names
                - List of file names that were retrieved (for citation formatting)
        """
        # Map point_id to summary
        summaries = {}
        file_names = []  # Track file names for citation formatting

        async def process_point_id(point_id: str):
            # Get file name to check if we've already retrieved this document
            file_name = point_id_to_file_name.get(point_id, "unknown") if point_id_to_file_name else "unknown"
            
            # Check if we've already retrieved this file (not just this point_id)
            if file_name in self.internal_sources:
                return "[SYSTEM NOTICE] You have already retrieved this document."

            # Check cache first
            cached_content = await self.internal_browse_manager.get_cached_document(point_id)

            if cached_content:
                logger.debug(f"Cache hit for {point_id}!")
                raw_content = cached_content
            else:
                logger.debug(f"Retrieving {'chunk' if use_surrounding else 'document'} {point_id} from Qdrant...")

                try:
                    # Choose endpoint based on retrieval mode
                    endpoint = f"documents/{point_id}/surrounding" if use_surrounding else f"documents/{point_id}"
                    params = {"max_chars": max_chars} if use_surrounding else {}

                    # Acquire lock to prevent duplicate retrievals
                    async with self.internal_browse_manager.acquire_retrieval_lock(point_id):
                        # Check cache again after acquiring lock (another agent may have populated it)
                        cached_content = await self.internal_browse_manager.get_cached_document(point_id, wait_for_current_retrieval=False)

                        if cached_content:
                            logger.debug(f"Cache hit after lock acquired for {point_id}!")
                            raw_content = cached_content
                        else:
                            result = await self._query_qdrant_api(endpoint, params)

                            if not result["success"]:
                                raise RuntimeError(f"Failed to retrieve {'chunk' if use_surrounding else 'document'} {point_id}: {result.get('error', 'Unknown error')}")

                            # Extract content from response
                            document_data = result["data"]
                            raw_content = document_data.get("content", "")

                            if not raw_content:
                                raise RuntimeError(f"Empty content retrieved for point {point_id}")

                            logger.debug(f"Successfully retrieved {'chunk' if use_surrounding else 'document'} {point_id}")
                            logger.debug(f"Content preview: {raw_content[:200]}")

                            # Add to cache
                            self.internal_browse_manager.add_to_cache(point_id, raw_content)

                except Exception as e:
                    traceback.print_exc()
                    self.failed_browses.append(f"internal:{point_id}")
                    return f"Error reading internal {'chunk' if use_surrounding else 'document'} {point_id}: {str(e)}"

            try:
                # Get file name for citation
                file_name = point_id_to_file_name.get(point_id, "unknown") if point_id_to_file_name else "unknown"
                if file_name not in file_names:
                    file_names.append(file_name)

                # Use shared chunking and summarization logic
                summarized = await self.chunk_and_summarize(
                    raw_content
                )

                # Track by file name instead of point_id to avoid counting multiple chunks as separate sources
                if file_name not in self.internal_sources:
                    self.internal_sources.append(file_name)
                logger.debug(f"After adding to internal source list:")
                logger.debug(f"{'\n'.join([f'- {item}' for item in self.internal_sources])}")
                # Include file name in summary for citation formatting
                summaries[point_id] = {
                    "file_name": file_name,
                    "summary": summarized
                }

            except Exception as e:
                traceback.print_exc()
                self.failed_browses.append(f"internal:{point_id}")
                return f"Error reading internal {'chunk' if use_surrounding else 'document'} {point_id}: {str(e)}"

        # Process in parallel or sequence depending on the configuration
        if config.is_parallel_mode_enabled():
            await asyncio.gather(*[process_point_id(point_id) for point_id in point_ids])
        else:
            for point_id in point_ids:
                await process_point_id(point_id)

        return json.dumps(summaries, indent=2), file_names

    async def _should_continue_research(self) -> bool:
        """
        Determines whether the research should continue or can be terminated early.
        
        Uses an LLM call to evaluate if the current summary sufficiently addresses
        the research topic. For simple questions with complete answers, returns False
        to end early. For complex/long-form topics, returns True to continue gathering
        sources.
        
        Returns:
            bool: True if research should continue, False if it can end early
        """
        continue_research_prompt = f"""
You are an evaluator of research completeness. Your task is to decide whether a deep research session should continue or end early.

Given a research topic and the current summary of gathered information, determine if:
1. The question can be answered simply and the answer is already included in the summary → End research (return False)
2. The topic is long-form/open-ended and requires more diverse sources → Continue research (return True)

Guidelines:
- For factual questions (e.g., "What is X?", "When did Y happen?"), if the answer is clearly stated, end early.
- For exploratory questions (e.g., "What are the opinions on...", "Compare X and Y", "Analyze the impact of..."), continue gathering sources.
- If the summary is empty or lacks key information mentioned in the topic, continue.
- If the summary has comprehensive coverage for a simple question, end early.
- When in doubt, prefer to continue for complex topics.

Respond with ONLY "CONTINUE" or "END", nothing else.

Examples:

Example 1:
Research topic: "What is the capital of France?"
Current summary: "The capital of France is Paris [1]."
Response: END

Example 2:
Research topic: "What is the CVE for the NiceCurl vulnerability?"
Current summary: "The NiceCurl vulnerability is tracked as CVE-2024-33663 [1]. It affects curl and libcurl versions before 8.6.0."
Response: END

Example 3:
Research topic: "What are the opinions on Google's new product, Antigravity?"
Current summary: "Google's Antigravity product has received mixed reviews. Some praise its innovative approach [1], while others express concerns about privacy [2]."
Response: CONTINUE

Example 4:
Research topic: "Compare the security features of AWS and Azure"
Current summary: "AWS offers IAM, KMS, and Security Hub [1]. Azure provides Azure AD, Key Vault, and Security Center [2]."
Response: CONTINUE

Example 5:
Research topic: "Who discovered penicillin?"
Current summary: "Penicillin was discovered by Alexander Fleming in 1928 [1]."
Response: END

Example 6:
Research topic: "What are the recent activities of APT42?"
Current summary: "APT42 has been observed using NICECURL backdoor in recent campaigns targeting cloud infrastructure [1][2]."
Response: CONTINUE

---

Research topic: {self.research_topic}
Current summary: {self.summary}

Response:
""".strip()

        try:
            response = await call_llm(
                self.client,
                self.model,
                "You are an evaluator that responds with ONLY 'CONTINUE' or 'END'.",
                continue_research_prompt,
            )
            
            response_text = (response.content or "").strip().upper()
            
            # Default to continuing if response is unclear
            if "END" in response_text and "CONTINUE" not in response_text:
                logger.debug(f"LLM decided to END research early")
                return False
            else:
                logger.debug(f"LLM decided to CONTINUE research")
                return True
                
        except Exception as e:
            logger.error(f"Error in _should_continue_research: {e}")
            # On error, default to continuing to avoid premature termination
            return True

    async def _run_internet_research(self, priority_queue: deque, source_limit: int):
        """
        Run internet-based research (web search + webpage browsing).

        Args:
            priority_queue: Queue of priority sources to search
            source_limit: Maximum number of sources to collect
        """
        max_retries = 3
        base_delay = 1.0  # Base delay in seconds for backoff

        while len(self.source_list) < source_limit or count_tokens(
            self.summary
        ) > int(MODEL_MAX_TOKENS * 0.8):
            self.num_rounds += 1

            # Search
            used_queries_formatted = (
                "\n".join([f"- {q}" for q in self.used_web_search_queries]) or "None"
            )

            # Check if any sites left in the priority queue
            if len(priority_queue):
                priority_item = priority_queue.popleft()
                # If there are sources left to prioritize, bypass the agent call and do deterministic search query first
                _, site = priority_item
                search_query = f"site:{site} {self.research_topic}"
                logger.debug(f"Bypassing LLM call for search query: {search_query}")
                search_results = await self.web_search(search_query)
            else:
                search_prompt = f"Research topic: {self.research_topic}\n\nUsed search queries:\n{used_queries_formatted}"
                
                # Retry loop for web search tool call
                search_results = None
                for attempt in range(max_retries):
                    search_msg = await call_llm(
                        self.client,
                        self.model,
                        WEB_SEARCH_INSTRUCTIONS,
                        search_prompt,
                        tools=[self.web_search],
                        force_tool=self.web_search,
                    )

                    search_tool_calls = search_msg.tool_calls
                    if search_tool_calls:
                        search_tool_call = search_tool_calls[0]
                        search_results = await self.web_search(
                            **json.loads(search_tool_call.function.arguments)
                        )
                        break
                    else:
                        logger.warning(f"Web search tool call failed (attempt {attempt + 1}/{max_retries}): LLM returned non-tool response")
                        if attempt < max_retries - 1:
                            exponential_delay = base_delay * (2 ** attempt)
                            jitter = random.uniform(0, exponential_delay * 0.5)
                            delay = exponential_delay + jitter
                            logger.debug(f"Retrying web search in {delay:.2f}s...")
                            await asyncio.sleep(delay)
                
                if not search_results:
                    raise RuntimeError(f"Web Search failed after {max_retries} attempts")
                    
            logger.debug(f"Web search results:\n{search_results}")

            # Browse webpages
            browse_prompt = f"Research topic: {self.research_topic}\n\nExisting references:\n{self.source_list}\n\nWeb search results:\n{search_results}"
            
            # Retry loop for webpage browse tool call
            browsed_contents = None
            for attempt in range(max_retries):
                logger.debug(attempt)
                browse_msg = await call_llm(
                    self.client,
                    self.model,
                    WEBPAGE_BROWSE_INSTRUCTIONS,
                    browse_prompt,
                    tools=[self.webpage_browse],
                    force_tool=self.webpage_browse,
                )

                browse_tool_calls = browse_msg.tool_calls
                if browse_tool_calls:
                    browse_tool_call = browse_tool_calls[0]
                    browse_arguments = json.loads(browse_tool_call.function.arguments)
                    
                    # Limit the number of pages to browse.
                    urls = browse_arguments.get("urls")
                    
                    if isinstance(urls, list):
                        # Limit the number of pages to browse if it's a list (and it should be!)
                        browse_limit = int(os.environ.get("NUM_BROWSE_PER_SEARCH", 2))
                        browse_arguments["urls"] = urls[:browse_limit]
                        logger.debug(f"Limiting browse to {len(browse_arguments["urls"])} pages.")

                    browsed_contents = await self.webpage_browse(**browse_arguments)
                    break
                else:
                    logger.warning(f"Webpage browse tool call failed (attempt {attempt + 1}/{max_retries}): LLM returned non-tool response")
                    if attempt < max_retries - 1:
                        exponential_delay = base_delay * (2 ** attempt)
                        jitter = random.uniform(0, exponential_delay * 0.5)
                        delay = exponential_delay + jitter
                        logger.debug(f"Retrying webpage browse in {delay:.2f}s...")
                        await asyncio.sleep(delay)
            
            if not browsed_contents:
                raise RuntimeError(f"Webpage browse tool call failed after {max_retries} attempts")

            # Summary update
            summary_prompt = f"Research topic: {self.research_topic}\n\nCurrent summary: {self.summary}\n\nNewly browsed contents: {json.dumps(browsed_contents)}"
            msg = await call_llm(
                self.client, self.model, REPORT_AGENT_INSTRUCTIONS, summary_prompt
            )
            logger.debug(f"Turn {self.num_rounds} Summary Prompt:")
            self.summary = msg.content or self.summary

            logger.info(f"Turn {self.num_rounds} summary update complete.")
            logger.info(f"Summary: {self.summary}")
            logger.debug(
                f"Sources used: {'\n'.join([f'- {item}' for item in self.source_list])}"
            )

            # Check if research should continue or end early
            if len(self.source_list) >= 1:
                should_continue = await self._should_continue_research()
                if not should_continue:
                    logger.info("LLM decided to end research early - sufficient information gathered")
                    break

    async def _run_internal_research(self, source_limit: int):
        """
        Run internal document research (Qdrant search + document retrieval).

        Strategy:
        - For files with 3 or more chunks scoring > 0.4: Read the full document (top 3 files)
        - For other files: Read surrounding chunks for points with score > 0.4

        Stop conditions (any of these will end the research):
        - Reached source_limit
        - No more unique files available to retrieve
        - Summary exceeds token limit
        - Search returns no results

        Args:
            source_limit: Maximum number of sources to collect
        """
        SCORE_THRESHOLD = 0.4
        HIGH_CONFIDENCE_MIN_CHUNKS = 2
        retrieved_file_hashes = set()  # Track unique files retrieved
        max_retries = 3
        base_delay = 1.0  # Base delay in seconds for backoff

        # Continue until we have enough sources, run out of files, or summary is too long
        while len(self.internal_sources) < source_limit:
            # Check if summary has exceeded token limit
            if count_tokens(self.summary) > int(MODEL_MAX_TOKENS / 5 * 4):
                logger.info("Summary exceeded token limit, ending internal research")
                break

            self.num_rounds += 1

            # Internal search
            used_internal_queries_formatted = (
                "\n".join([f"- {q}" for q in self.used_internal_search_queries]) or "None"
            )

            search_prompt = f"Research topic: {self.research_topic}\n\nUsed internal search queries:\n{used_internal_queries_formatted}"
            
            # Retry loop for internal search tool call
            search_results_raw = None
            for attempt in range(max_retries):
                search_msg = await call_llm(
                    self.client,
                    self.model,
                    INTERNAL_SEARCH_INSTRUCTIONS,
                    search_prompt,
                    tools=[self.internal_search],
                    force_tool=self.internal_search,
                )

                search_tool_calls = search_msg.tool_calls
                if search_tool_calls:
                    search_tool_call = search_tool_calls[0]
                    search_results_raw = await self.internal_search(
                        **json.loads(search_tool_call.function.arguments)
                    )
                    break
                else:
                    logger.warning(f"Internal search tool call failed (attempt {attempt + 1}/{max_retries}): LLM returned non-tool response")
                    if attempt < max_retries - 1:
                        exponential_delay = base_delay * (2 ** attempt)
                        jitter = random.uniform(0, exponential_delay * 0.5)
                        delay = exponential_delay + jitter
                        logger.debug(f"Retrying internal search in {delay:.2f}s...")
                        await asyncio.sleep(delay)
            
            if not search_results_raw:
                logger.warning("Internal search tool not called after retries, ending internal research")
                break

            # Parse search results and group by file
            try:
                search_results_data = json.loads(search_results_raw)
                logger.debug("Qdrant results:")
                logger.debug(search_results_data)
                if isinstance(search_results_data, list):
                    # Group results by file_hash with detailed score information
                    file_infos = self._group_qdrant_results_by_file(
                        search_results_data,
                        score_threshold=SCORE_THRESHOLD
                    )
                else:
                    logger.warning(f"Unexpected search results format: {search_results_data}")
                    break
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse search results: {e}")
                break

            if not file_infos:
                logger.warning("No search results found, ending internal research")
                break

            # Filter out files we've already retrieved
            new_file_infos = [f for f in file_infos if f["file_hash"] not in retrieved_file_hashes]

            if not new_file_infos:
                logger.info("All available files have been retrieved, ending internal research")
                break

            logger.info(f"Found {len(new_file_infos)} new files to retrieve (out of {len(file_infos)} total)")

            # Determine retrieval strategy based on chunk scores
            point_ids_to_retrieve = []

            # Check if any file has 3 or more chunks with score > threshold
            high_confidence_files = [
                f for f in new_file_infos 
                if len(f["high_scoring_point_ids"]) >= HIGH_CONFIDENCE_MIN_CHUNKS
            ]

            if high_confidence_files:
                # Strategy 1: Read full documents for top high-confidence files
                logger.info(f"Found {len(high_confidence_files)} high-confidence files (>={HIGH_CONFIDENCE_MIN_CHUNKS} chunks with score > {SCORE_THRESHOLD}), reading full documents")
                # Take top 3 files by total score
                for file_info in high_confidence_files[:3]:
                    point_ids_to_retrieve.append(file_info["first_point_id"])
                    retrieved_file_hashes.add(file_info["file_hash"])
                use_surrounding = False
            else:
                # Strategy 2: Read surrounding chunks for high-scoring points
                # IMPORTANT: Only take ONE chunk per file to avoid duplicate summarization
                logger.info(f"No high-confidence files found, reading surrounding chunks for points with score > {SCORE_THRESHOLD}")
                for file_info in new_file_infos:
                    # Take only the highest-scoring point from each file
                    if file_info["high_scoring_point_ids"]:
                        # Get the point with highest score from this file
                        best_point_id = max(
                            file_info["high_scoring_point_ids"],
                            key=lambda pid: file_info["point_scores"].get(pid, 0)
                        )
                        point_ids_to_retrieve.append(best_point_id)
                        retrieved_file_hashes.add(file_info["file_hash"])
                use_surrounding = True

            if not point_ids_to_retrieve:
                logger.warning("No point IDs to retrieve")
                break

            logger.debug(f"Retrieving {len(point_ids_to_retrieve)} points (use_surrounding={use_surrounding})")
            logger.debug(f"Point IDs: {point_ids_to_retrieve}")

            # Build point_id to file_name mapping for citation formatting
            point_id_to_file_name = {}
            for file_info in new_file_infos:
                for pid in file_info["all_point_ids"]:
                    point_id_to_file_name[pid] = file_info["file_name"]

            # Browse internal documents directly with calculated point IDs
            # Note: We bypass LLM for point ID selection to prevent hallucination
            browsed_contents, retrieved_file_names = await self.internal_browse(
                point_ids=point_ids_to_retrieve,
                use_surrounding=use_surrounding,
                point_id_to_file_name=point_id_to_file_name
            )

            # Summary update - include file names for citation formatting
            summary_prompt = f"Research topic: {self.research_topic}\n\nCurrent summary: {self.summary}\n\nNewly retrieved internal documents: {browsed_contents}\n\nRetrieved file names: {retrieved_file_names}"
            msg = await call_llm(
                self.client, self.model, REPORT_AGENT_INSTRUCTIONS, summary_prompt
            )
            logger.debug(f"Turn {self.num_rounds} Summary Prompt:")
            self.summary = msg.content or self.summary

            logger.info(f"Turn {self.num_rounds} summary update complete.")
            logger.info(f"Summary: {self.summary}")
            logger.debug(
                f"Internal sources used: {'\n'.join([f'- {item}' for item in self.internal_sources])}")
            logger.debug(
                f"Unique file hashes retrieved: {len(retrieved_file_hashes)}"
            )

            # Check if research should continue or end early
            if len(self.source_list) >= 1:
                should_continue = await self._should_continue_research()
                if not should_continue:
                    logger.info("LLM decided to end research early - sufficient information gathered")
                    break

    async def run(self, research_topic: str, min_sources: Optional[int] = None):
        """
        Contains the main deep research logic.
        If there are sources returned from priority_sources() method,
        those sources will always be used in the search before moving on to free searching.
        
        Supports three modes:
        - INTERNET: Web search + webpage browsing only
        - INTERNAL: Qdrant internal document search + retrieval only
        - HYBRID (default): Both internet and internal research in sequence

        Args:
            research_topic (str): Topic to research on
            min_sources (Optional[int]): Minimum number of sources; defaults to source_limit() as defined by class
        """
        self.research_topic = research_topic

        # Queue priority sources (for internet research)
        priority_queue = deque(self.priority_sources().items())

        source_limit = min_sources or self.source_limit()

        if self.mode == ResearchMode.INTERNET:
            logger.info("Running in INTERNET mode")
            await self._run_internet_research(priority_queue, source_limit)
        elif self.mode == ResearchMode.INTERNAL:
            logger.info("Running in INTERNAL mode")
            await self._run_internal_research(source_limit)
        elif self.mode == ResearchMode.HYBRID:
            logger.info("Running in HYBRID mode")
            # Run internet research first
            await self._run_internet_research(priority_queue, source_limit)
            # Then run internal research
            await self._run_internal_research(source_limit)

        # Form the final summary
        errors_section = ""
        if len(self.failed_browses):
            errors_section = f"\n\n**Error Browsing URLs**\n{'\n'.join([f'{index + 1}. {item}' for index, item in enumerate(self.failed_browses)])}"

        self.summary = f"{self.summary}{errors_section if errors_section else ''}"

        return self.summary
