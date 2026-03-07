import asyncio
import time
import json
import logging
import os
import httpx
from pathlib import Path
from typing import Optional, Any, Dict
from openai import AsyncOpenAI
from geo_deepresearch.util.tokens import count_tokens
from geo_deepresearch.util.tools import function_to_schema
from geo_deepresearch.config import config
from geo_deepresearch.util.logging import get_logger
from geo_deepresearch.util.llm import call_llm, openai_client, openai_default_model

logger = get_logger()

MODEL_MAX_TOKENS = int(os.environ.get("DEEP_RESEARCH_MODEL_MAX_TOKENS", 100000))

PRIORITIZE_SOURCES_SUFFIX = """
---

Prioritize these sources for APT information:
- Information on APTs: https://cloud.google.com
"""

WEB_SEARCH_INSTRUCTIONS = f"""
Given web search tool, perform web search to find information on the given research topic.
As it uses Google search under the hood, you should use advanced operators like "site:", "intitle", etc. where necessary.
Search specifically from prioritized sources using the `site:` prefix if they are not referenced yet (e.g. site:cloud.google.com APT42 IOCs).
The user will provide a list of used queries, avoid repeated searches.

{PRIORITIZE_SOURCES_SUFFIX}
""".strip()

WEBPAGE_BROWSE_INSTRUCTIONS = f"""
Given a research topic and web search results from previous agent, rank the top 3 webpages with relevance to the research topic, then browse them.
The user may provide a list of existing citations, avoid browsing those websites.

{PRIORITIZE_SOURCES_SUFFIX}
""".strip()

SUMMARY_AGENT_INSTRUCTIONS = """
You are an expert in CTI, Cyber Threat Intelligence deep research.
You will be given a query related to CTI, along with a summary of the findings so far.
Given the web search and webpage browsing tool results, add to the existing citation list and summary using information from the previous tool results.
You should only extract out information relevant to the user's query for updating the summary.
Deduplicate information as necessary.
All statements in your answer must be linked to a citation.
Ensure to keep all previously linked citations and references list.

---

Refer to example response below, but be more detailed where necessary.

--- Start of example ---
IOCs found:
- www.badsite.com [1]
- 162.108.0.2 [2]

References:
1. https://cloud.google.com/blog/topics/...
2. https://www.citation2.com
--- End of example ---
""".strip()

# --- Main Class ---

class CtiAgentRunner:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.environ.get("DEEP_RESEARCH_API_KEY"),
            base_url=os.environ.get("DEEP_RESEARCH_BASE_URL")
        )
        self.model = os.environ.get("DEEP_RESEARCH_MODEL", "z-ai/glm-4.7-flash")
        
        self.source_list = []
        self.failed_browses = []
        self.used_web_search_queries = []
        self.num_turns = 0
        self.research_topic = ""
        self.summary = "No research done yet"
        
        self.jina_api_key = os.environ.get("JINA_API_KEY", "")
        self.jina_timeout = 60.0
        self.remaining_token_count = int(os.environ.get("DEEP_RESEARCH_MODEL_MAX_TOKENS", 100000))

        # Register tools for introspection
        self.available_tools = {
            "web_search": self.web_search,
            "webpage_browse": self.webpage_browse
        }
        self.tools_schema = [function_to_schema(f) for f in self.available_tools.values()]

    def _token_count_to_word_count(self, token_count: int):
        return int(token_count / 1.3)

    def _word_count_to_token_count(self, word_count: int) -> int:
        return int(word_count * 1.3)

    async def _make_serper_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
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
            # if self.date_range:
            #     params["tbs"] = self.date_range
            # if self.location:
            #     params["gl"] = self.location

            # if self.language:
            #     params["hl"] = self.language

            logger.debug(f"Making request to {url} with params: {params}")
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=params, timeout=15.0)
                response.raise_for_status()

                logger.debug(f"Successfully received response from {endpoint} endpoint")
                return {"success": True, "data": response.json(), "raw_response": response.text}
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
                return json.dumps({"error": "Please provide a query to search for"}, indent=2)
            
            # Cache query
            self.used_web_search_queries.append(query)

            logging.debug(f"Searching Google for: {query}")

            params = {
                "q": query,
                "num": num_results or 5,
            }

            result = await self._make_serper_request("search", params)

            if result["success"]:
                logger.debug(f"Successfully found Google search results for query: {query}")
                return result["raw_response"]
            else:
                logger.error(f"Error searching Google for query {query}: {result['error']}")
                return json.dumps({"error": result["error"]}, indent=2)

        except Exception as e:
            logger.error(f"Unexpected error searching Google for query {query}: {e}")
            return json.dumps({"error": f"An unexpected error occurred: {str(e)}"}, indent=2)

    def _semantic_chunker(self, text, max_tokens=7000, overlap=500):
        """
        Splits text into chunks at natural boundaries with overlap to preserve context.
        """
        chunks = []
        words = text.split()

        # Approximate word counts (Words = Tokens / 1.3)
        words_per_chunk = int(max_tokens / 1.3)
        overlap_words = int(overlap / 1.3)

        start = 0
        while start < len(words):
            end = start + words_per_chunk
            chunk_words = words[start:end]

            # Join and return the chunk
            chunks.append(" ".join(chunk_words))

            # Slide forward, but move back by the overlap amount
            start += words_per_chunk - overlap_words

            # Safety break to avoid infinite loops
            if start >= len(words) or words_per_chunk <= overlap_words:
                break

        return chunks

    def _get_jina_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "X-With-Links-Summary": "true",
            "X-With-Images-Summary": "true",
        }
        if self.jina_api_key:
            headers["Authorization"] = f"Bearer {self.jina_api_key}"
        if self.jina_timeout:
            headers["X-Timeout"] = str(self.jina_timeout)

        return headers
    
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
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(full_url, headers=self._get_jina_headers(), timeout=self.jina_timeout)

                response.raise_for_status()
                jina_response = response.json()
                # Jina JSON structure usually has content in 'data', 'content', or 'markdown'
                jina_data = jina_response.get("data", jina_response)

                # print(f"[DEBUG] Jina data:\n{json.dumps(jina_data, indent=2)}")
                logger.debug(f"Jina data:\n{json.dumps(jina_data, indent=2)}")
                raw_webpage_content = jina_data.get("content", "")
                logger.debug(f"Raw webpage content: {raw_webpage_content}")

                # --- START: RAG-Inspired Semantic Chunking ---
                incoming_tokens = count_tokens(raw_webpage_content)

                if incoming_tokens > 10000:
                    print(
                        f"[DEBUG] Megapage detected ({incoming_tokens} tokens). Processing in chunks..."
                    )
                    # We use overlap so the model doesn't lose context between chunks
                    chunks = self._semantic_chunker(
                        raw_webpage_content, max_tokens=7000, overlap=500
                    )

                    # Semantic chunker sometimes only returns 1 chunk, in this case don't need to do aggregation of summaries
                    if len(chunks) > 1:
                        intermediate_summaries = []
                        for i, chunk in enumerate(chunks):
                            print(f"[DEBUG] Processing chunk {i+1}/{len(chunks)}...")
                            # Each chunk gets a fixed budget for its mini-summary
                            chunk_summary = await self.summarize_webpage(chunk, 1000)
                            logger.debug(f"Summary for chunk {i+1}: {chunk_summary}")
                            intermediate_summaries.append(chunk_summary)

                        # Consolidate: This becomes the new input for the final update
                        raw_webpage_content = "\n\n--- NEXT SECTION ---\n\n".join(
                            intermediate_summaries
                        )
                # --- END: Chunking ---

                # Budgeting Logic
                MIN_SUMMARY_ROOM = 150
                buffer_tokens = self._word_count_to_token_count(200)
                current_summary_size = count_tokens(self.summary) if self.summary else 0

                if self.num_turns == 0:
                    # 3/4 of remaining token count
                    summarize_max_tokens = int(self.remaining_token_count / 4 * 3)
                else:
                    available_space = (
                        self.remaining_token_count - current_summary_size - buffer_tokens
                    )
                    summarize_max_tokens = max(available_space, MIN_SUMMARY_ROOM)

                logger.debug(f"Budgeting {summarize_max_tokens} tokens for this intermediate summary.")
                logger.debug(f"Passing in for final summarization: {raw_webpage_content}")
                summarized = await self.summarize_webpage(
                    raw_webpage_content, summarize_max_tokens
                )

                self.source_list.append(url)
                logger.debug(f"After adding to source list:")
                logger.debug(f"{'\n'.join([f'- {item}' for item in self.source_list])}")
                summaries[url] = summarized

            except Exception as e:
                import traceback
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

    async def summarize_webpage(self, contents: str, recommended_max_tokens: int) -> str:
        # Max tokens is used for recommended word limit calculation, not a hard cap
        recommended_word_limit = self._token_count_to_word_count(recommended_max_tokens)

        summarizer_instructions = f"""
Given the following research topic and webpage contents, extract out only the information relevant to the query.
The webpage contents may be truncated. If it seems truncated, summarize while noting a possible lack of context due truncation.
Be concise to save tokens, but summarize in a way that the agent receiving your summary can understand it without extra context.
The data might be chunked; if it is, ensure to deduplicate information, as there is some overlap to avoid loss of context
Estimated word count limit: {recommended_word_limit}.
Use the word count limit as a guideline on how concise you must be.
        """.strip()
        user_prompt = f"Query: {self.research_topic}\n\nWebpage contents:\n\n{contents}"
        res = await call_llm(openai_client, openai_default_model, summarizer_instructions, user_prompt)
        if not res.content:
            logger.error("Unexpected empty summarization. Response here:")
            logger.error(res)
        return res.content or ""

    def _generate_report_output_path(self, file_name_base: Optional[str] = None, ext: str = "md") -> Path:
        save_dir = Path('./outputs').absolute()
        filename = f"{file_name_base if file_name_base else int(time.time())}.{ext}"
        return save_dir / filename

    def _save_report(self, file_contents: str, file_name_base: Optional[str] = None, ext: str = "md") -> Path:
        # Ensure directory exists
        path = self._generate_report_output_path(file_name_base=file_name_base, ext=ext)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            f.write(file_contents)
        
        return path

    async def run(self, research_topic: str):
        self.research_topic = research_topic
        
        # TODO: Better end condition, and differentiate the cause of stopping the research for logging
        while (len(self.source_list) < 5 or count_tokens(self.summary) > int(MODEL_MAX_TOKENS / 5 * 4)):
            self.num_turns += 1

            # Search
            queries_formatted = '\n'.join([f"- {q}" for q in self.used_web_search_queries]) or "None"
            search_prompt = f"Research topic: {self.research_topic}\n\nUsed search queries:\n{queries_formatted}"
            search_msg = await call_llm(self.client, self.model, WEB_SEARCH_INSTRUCTIONS, search_prompt, tools=[self.web_search], force_tool=self.web_search)
            
            # print("[DEBUG]: Tool calls for search:")
            search_tool_calls = search_msg.tool_calls
            if not search_tool_calls:
                raise RuntimeError("Web Search failed")
            # print(search_msg.tool_calls)
            search_tool_call = search_tool_calls[0]
            search_results = await self.web_search(**json.loads(search_tool_call.function.arguments))
            logger.debug(f"Web search results:\n{search_results}")

            # Browse webpages
            browse_prompt = f"Research topic: {self.research_topic}\n\nExisting references:\n{self.source_list}\n\nWeb search results:\n{search_results}"
            browse_msg = await call_llm(self.client, self.model, WEBPAGE_BROWSE_INSTRUCTIONS, browse_prompt, tools=[self.webpage_browse], force_tool=self.webpage_browse)
            logger.debug(browse_prompt)
            
            # print("[DEBUG]: Tool calls for browse:")
            # print(browse_msg.tool_calls)
            browse_tool_calls = browse_msg.tool_calls
            if not browse_tool_calls:
                raise RuntimeError("Web Search failed")
            browse_tool_call = browse_tool_calls[0]
            browse_arguments = json.loads(browse_tool_call.function.arguments)
            browsed_contents = await self.webpage_browse(**browse_arguments)

            # Summary update
            summary_prompt = f"Research topic: {self.research_topic}\n\nCurrent summary: {self.summary}\n\nNewly browsed contents: {json.dumps(browsed_contents)}"
            msg = await call_llm(self.client, self.model, SUMMARY_AGENT_INSTRUCTIONS, summary_prompt)
            logger.debug(f"Turn {self.num_turns} Summary Prompt:")
            self.summary = msg.content or self.summary
            
            logger.info(f"Turn {self.num_turns} summary update complete.")

            logger.info(f"Summary: {self.summary}")

            # Source list
            logger.debug(f"Sources used: {'\n'.join([f'- {item}' for item in self.source_list])}")

        # Form the final summary
        errors_section = ""
        if len(self.failed_browses):
            errors_section = f"\n\n**Errors Browsing URLs**\n\n{'\n'.join([f'{index + 1}. {item}' for index, item in enumerate(self.failed_browses)])}"
        
        self.summary = f"{self.summary}{errors_section if errors_section else ''}"

        # Save to file
        path = self._save_report(self.summary)
        logger.info(f"Saved to: {path.absolute()}")

        return self.summary
