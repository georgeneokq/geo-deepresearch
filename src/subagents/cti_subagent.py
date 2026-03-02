import asyncio
import json
import logging
import os
import httpx
from typing import Optional, Any, Dict, List, Callable
from openai import AsyncOpenAI
from util.tokens import count_tokens
from util.tools import function_to_schema
from tools.time import append_current_datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

MODEL_MAX_TOKENS = int(os.environ.get("DEEP_RESEARCH_MODEL_MAX_TOKENS", 100000))

PRIORITIZE_SOURCES_SUFFIX = """
---

Prioritize sources:
- Google cloud: https://cloud.google.com
"""

WEB_SEARCH_INSTRUCTIONS = f"""
Given web search tool, perform web search to find information on the given research topic.
Keep your search queries concise.
Search specifically from prioritized sources using the site: prefix if they are not referenced yet.
The user will provide a list of used queries, avoid repeated searches.

{PRIORITIZE_SOURCES_SUFFIX}
""".strip()

WEBPAGE_BROWSE_INSTRUCTIONS = f"""
Given a research topic and web search results from previous agent, rank the top 3 webpages with relevance to the research topic, then browse them.
The user will provide a list of existing references, avoid browsing those websites.

{PRIORITIZE_SOURCES_SUFFIX}
""".strip()

SUMMARY_AGENT_INSTRUCTIONS = """
You are an expert in CTI, Cyber Threat Intelligence deep research.
You will be given a query related to CTI, along with a summary of the findings so far.
Given the web search and webpage browsing tool results, update the current summary with information from the previous tool results.
You should only extract out information relevant to the user's query for updating the summary.
Deduplicate information as necessary.
All statements in your answer must be linked to a citation.

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
        self.used_web_search_queries = []
        self.num_turns = 0
        self.research_topic = ""
        self.summary = "No research done yet"
        
        self.jina_api_key = os.environ.get("JINA_API_KEY", "")
        self.jina_timeout = 30.0
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

    async def _call_llm(
        self, 
        system: str, 
        user: str, 
        tools: Optional[List[Callable]] = None, 
        force_tool: Optional[Callable] = None, 
        max_tokens: Optional[int] = None, 
        temperature: float = 0.6
    ) -> Any:
        """
        Standardized LLM call that introspects Python functions on the fly.
        """
        messages = [
            {"role": "system", "content": append_current_datetime(system)},
            {"role": "user", "content": user}
        ]
        
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens: 
            kwargs["max_tokens"] = max_tokens
            
        # Handle on-the-fly tool introspection
        if tools:
            kwargs["tools"] = [function_to_schema(f) for f in tools]
            print(kwargs["tools"])
            
        # Handle tool forcing
        if force_tool:
            # If force_tool is passed but not in tools list, add it automatically
            if not tools or force_tool not in tools:
                kwargs.setdefault("tools", []).append(function_to_schema(force_tool))
            
            kwargs["tool_choice"] = {
                "type": "function", 
                "function": {"name": force_tool.__name__}
            }
        
        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message

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
            print(f"[DEBUG] Browsing {full_url}")
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
                logger.debug(f"Passing in for intermediate summarization: {raw_webpage_content}")
                summarized = await self.summarize_webpage(
                    raw_webpage_content, summarize_max_tokens
                )

                self.source_list.append(url)
                logger.debug(f"After adding to source list:")
                logger.debug(f"Sources used: {'\n'.join([f'- {item}' for item in self.source_list])}")
                summaries[url] = summarized

            except Exception as e:
                import traceback
                traceback.print_exc()
                return f"Error reading URL: {str(e)}"
        
        # Browse in parallel
        asyncio.gather(*[process_url(url) for url in urls])

        return summaries

    async def summarize_webpage(self, contents: str, max_tokens: int) -> str:
        # Max tokens is used for recommended word limit calculation, not a hard cap
        recommended_word_limit = self._token_count_to_word_count(max_tokens)

        summarizer_instructions = f"""
Given the following research topic and webpage contents, extract out only the information relevant to the query.
Be concise to save tokens, but summarize in a way that the agent receiving your summary can understand it without extra context.
The data might be chunked; if it is, ensure to deduplicate information, as there is some overlap to avoid loss of context
Estimated word count limit: {recommended_word_limit}.
Use the word count limit as a guideline on how concise you must be.
        """.strip()
        user_prompt = f"Query: {self.research_topic}\n\nWebpage contents:\n\n{contents}"
        res = await self._call_llm(append_current_datetime(summarizer_instructions), user_prompt)
        if not res.content:
            logger.error("Unexpected empty summarization. Response here:")
            logger.error(res)
        return res.content or ""

    async def run(self, research_topic: str):
        self.research_topic = research_topic
        
        # TODO: Better end condition
        while len(self.source_list) < 5 or count_tokens(self.summary) > int(MODEL_MAX_TOKENS / 5 * 4):
            # Search
            queries_formatted = '\n'.join([f"- {q}" for q in self.used_web_search_queries]) or "None"
            search_prompt = f"Research topic: {self.research_topic}\n\nUsed search queries:\n{queries_formatted}"
            search_msg = await self._call_llm(WEB_SEARCH_INSTRUCTIONS, search_prompt, tools=[self.web_search], force_tool=self.web_search)
            
            # print("[DEBUG]: Tool calls for search:")
            # print(search_msg.tool_calls)
            tool_call = search_msg.tool_calls[0]
            search_results = await self.web_search(**json.loads(tool_call.function.arguments))
            logger.debug(f"Web search results:\n{search_results}")

            # Browse webpages
            # TODO: Update webpage browse to allow multiple browsing
            browse_prompt = f"Research topic: {self.research_topic}\n\nExisting references:\n{self.source_list}\n\nWeb search results:\n{search_results}"
            browse_msg = await self._call_llm(WEBPAGE_BROWSE_INSTRUCTIONS, browse_prompt, tools=[self.webpage_browse], force_tool=self.webpage_browse)
            
            # print("[DEBUG]: Tool calls for browse:")
            # print(browse_msg.tool_calls)
            tool_call = browse_msg.tool_calls[0]
            browse_arguments = json.loads(tool_call.function.arguments)
            print(browse_arguments)
            return
            browsed_contents = await self.webpage_browse(**browse_arguments)

            # Summary update
            summary_prompt = f"Research topic: {self.research_topic}\n\nReferences: {'\n'.join([f'- {item}' for item in self.source_list])}\n\nCurrent summary: {self.summary}\n\nNewly browsed contents: {json.dumps(browsed_contents)}"
            msg = await self._call_llm(SUMMARY_AGENT_INSTRUCTIONS, summary_prompt)
            self.summary = msg.content or self.summary
            
            self.num_turns += 1
            logger.info(f"Turn {self.num_turns} summary update complete.")

            logger.info(f"Summary: {self.summary}")

            # Source list
            logger.debug(f"Sources used: {'\n'.join([f'- {item}' for item in self.source_list])}")

        print("\n--- FINAL SUMMARY ---\n")
        print(self.summary)