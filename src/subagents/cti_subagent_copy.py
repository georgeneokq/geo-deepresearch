import json
import logging
import os
import httpx
from typing import Optional, Dict, Any
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.models.openai import OpenAILike
from agno.tools import tool, Toolkit
from util.tokens import count_tokens
from tools.time import append_current_datetime
from openai import AsyncOpenAI  # TODO: Refactor to use this

logger = logging.getLogger(__name__)

# Default 100k max tokens
MODEL_MAX_TOKENS = int(os.environ.get("DEEP_RESEARCH_MODEL_MAX_TOKENS", 100000))

web_search_agent_instructions = """
Given web search tool, perform web search to find information on the given research topic.
The user will provide a list of used queries, avoid repeated searches.

Current datetime:

"""

webpage_browse_agent_instructions = """
Given a research topic and web search results from previous agent, browse 3 webpages that seem most relevant to the topic.
The user will provide a list of existing references, avoid browsing those websites.

Current datetime:

"""

summary_agent_instructions = """
You are an expert in CTI, Cyber Threat Intelligence deep research.
You will be given a query related to CTI, along with a summary of the findings so far.
Given the web search and webpage browsing tool results, update the current summary with information from the previous tool results.
You should only extract out information relevant to the user's query for updating the summary.
Once you browse a webpage with useful information, you must respond with an updated summary of the findings.
Add on to the summary given to you by the user, but deduplicate information as necessary.
All statements in your answer must be linked to a citation.
Before you browse a webpage, ensure it is not in the list of already browsed webpages.

---

Prioritize sources:
- Google cloud: https://cloud.google.com

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

Current datetime:

""".strip()


# TODO: Abstract common logic into abstract class
class CtiAgentRunner:
    source_list: list[str]
    used_web_search_queries: list[str]
    current_token_usage: int
    remaining_token_count: int
    num_turns: int
    research_topic: str
    summary: str
    jina_api_key: str
    jina_timeout: int | None
    agent: Agent

    def __init__(self):
        self.source_list = []
        self.used_web_search_queries = []
        self.current_token_usage = 0
        self.remaining_token_count = 0
        self.num_turns = 0
        self.research_topic = ""
        self.summary = "No research done yet"
        self.jina_api_key = os.environ.get("JINA_API_KEY", "")
        jina_timeout = os.environ.get("JINA_TIMEOUT")
        self.jina_timeout = int(jina_timeout) if jina_timeout else None
        self.agent = self.create_summary_agent()

    def _token_count_to_word_count(self, token_count: int):
        """
        Estimates the number of words a certain number of tokens will occupy.
        """
        # Estimate the number of words it should be limited to.
        # In the world of LLMs (especially with modern tokenizers like Llama 3 or GLM), the industry-standard "rule of thumb" is:
        # 1,000 tokens approximates to 750 words (or 1 word approximates to 1.3 ~ 1.4 tokens)
        return int(token_count / 1.3)

    def _word_count_to_token_count(self, word_count: int) -> int:
        """
        Estimates the number of tokens a certain number of words will occupy.
        Reverse of _token_count_to_word_count.
        """
        # Using the same 1.3 ratio.
        # Example: 100 words * 1.3 = 130 tokens.
        return int(word_count * 1.3)

    async def summarize_webpage(self, contents: str, max_tokens: int) -> str:
        """
        Spawns an agent to summarize a webpage in relation to a given query.
        The agent will get rid of all information that is not related to the query
        """
        recommended_word_limit = self._token_count_to_word_count(max_tokens)

        summarizer_instructions = f"""
Given the following query and webpage contents, extract out only the information relevant to the query.
Be concise to save tokens, but summarize in a way that the agent receiving your summary can understand it without extra context.
The data might be chunked; if it is, ensure to deduplicate information, as there is some overlap to avoid loss of context
Estimated word count limit: {recommended_word_limit}.
Use the word count limit as a guideline on how concise you must be.
        """.strip()

        summarizer_agent = Agent(
            model=OpenAILike(
                id=os.environ.get("DEEP_RESEARCH_MODEL", "z-ai/glm-4.7-flash"),
                base_url=os.environ.get("DEEP_RESEARCH_BASE_URL"),
                api_key=os.environ.get("DEEP_RESEARCH_API_KEY"),
                temperature=0.6,
                max_tokens=max_tokens,
            ),
            instructions=summarizer_instructions,
        )

        user_prompt = f"Query: {self.research_topic}\n\nWebpage contents:\n{contents}"
        result: RunOutput = await summarizer_agent.arun(user_prompt)  # type:ignore

        if not isinstance(result.content, str):
            raise RuntimeError(
                f'Unexpected output from summarizer agent while processing "{self.research_topic}".'
            )

        return result.content
    
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
                response = await client.post(url, headers=headers, data=params)
                response.raise_for_status()

                logger.debug(f"Successfully received response from {endpoint} endpoint")
                return {"success": True, "data": response.json(), "raw_response": response.text}
        except Exception as e:
            logger.error(f"Serper API error: {str(e)}")
            return {"success": False, "error": str(e)}

    @tool(stop_after_tool_call=True)
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

    @tool(stop_after_tool_call=True)
    async def webpage_browse(self, url: str):
        if url in self.source_list:
            return "[SYSTEM NOTICE] You have already browsed this webpage."

        full_url = f"https://r.jina.ai/{url}"
        print(f"[DEBUG] Browsing {full_url}")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(full_url, headers=self._get_jina_headers())

            response.raise_for_status()
            jina_data = response.json()
            # Jina JSON structure usually has content in 'data', 'content', or 'markdown'
            # print(f"[DEBUG] Jina data:\n{json.dumps(jina_data, indent=2)}")
            raw_webpage_content = jina_data.get("content", "")

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
                    chunk_sum = await self.summarize_webpage(chunk, 800)
                    intermediate_summaries.append(chunk_sum)

                # Consolidate: This becomes the new input for the final update
                raw_webpage_content = "\n\n--- NEXT SECTION ---\n\n".join(
                    intermediate_summaries
                )
            # --- END: Chunking ---

            # Your updated Budgeting Logic
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

            print(f"[DEBUG] Budgeting {summarize_max_tokens} tokens for this summary.")
            summarized = await self.summarize_webpage(
                raw_webpage_content, summarize_max_tokens
            )

            self.source_list.append(url)
            return summarized

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Error reading URL: {str(e)}"

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
    
    def create_web_search_agent(self):
        web_search_agent = Agent(
            model=OpenAILike(
                id=os.environ.get("DEEP_RESEARCH_MODEL", "z-ai/glm-4.7-flash"),
                base_url=os.environ.get("DEEP_RESEARCH_BASE_URL"),
                api_key=os.environ.get("DEEP_RESEARCH_API_KEY"),
                temperature=0.8,
            ),
            instructions=append_current_datetime(web_search_agent_instructions),
            tools=[
                self.web_search,
            ],
            tool_call_limit=1,
            tool_choice="web_search"
        )
        return web_search_agent

    def create_webpage_browse_agent(self):
        webpage_browse_agent = Agent(
            model=OpenAILike(
                id=os.environ.get("DEEP_RESEARCH_MODEL", "z-ai/glm-4.7-flash"),
                base_url=os.environ.get("DEEP_RESEARCH_BASE_URL"),
                api_key=os.environ.get("DEEP_RESEARCH_API_KEY"),
                temperature=0.8,
            ),
            instructions=append_current_datetime(webpage_browse_agent_instructions),
            tools=[
                self.webpage_browse,
            ],
            tool_call_limit=3,
            tool_choice="webapge_browse"
        )
        return webpage_browse_agent

    def create_summary_agent(self):
        """
        Spawns a summary agent with expertise in Cyber Threat Intelligence deep research.
        """

        summary_agent = Agent(
            model=OpenAILike(
                id=os.environ.get("DEEP_RESEARCH_MODEL", "z-ai/glm-4.7-flash"),
                base_url=os.environ.get("DEEP_RESEARCH_BASE_URL"),
                api_key=os.environ.get("DEEP_RESEARCH_API_KEY"),
                temperature=0.8,
            ),
            instructions=append_current_datetime(summary_agent_instructions),
        )
        return summary_agent

    def reset_state(self):
        self.__init__()

    async def run(self, research_topic: str):
        """
        Asynchronously runs agent in a loop.
        Context is cleared at the end of each turn.
        """
        self.research_topic = research_topic

        print(f"[DEBUG] Processing research topic: {self.research_topic}")

        # Loop: Web Search -> Browse Webpages -> Update summary of findings -> Evaluate whether research is sufficient
        while True:
            # Re-initialize every round as the current datetime will be updated as context
            web_search_agent = self.create_web_search_agent()
            webpage_browse_agent = self.create_webpage_browse_agent()
            summary_agent = self.create_summary_agent()

            # Web search
            used_search_queries_portion = '\n'.join(['- {}'.format(query) for query in self.used_web_search_queries]) if len(self.used_web_search_queries) else "None"
            web_search_agent_prompt = f"Research topic: {self.research_topic}\n\nUsed search queries:\n{used_search_queries_portion}"
            web_search_agent_response: RunOutput = await web_search_agent.arun(web_search_agent_prompt)  # type: ignore
            web_search_content = web_search_agent_response.content
            print(f"Web search result:\n{web_search_content}")
            logger.debug(f"self.used_queries: {"\n".join([f"[{index + 1}] {search_query}" for index, search_query in enumerate(self.used_web_search_queries)])}")

            if not isinstance(web_search_content, str):
                logger.error("Error occured in web search. Retrying.")
                continue

            # Webpage browse
            webpage_browse_agent_prompt = f"Research topic: {self.research_topic}"
            webpage_browse_agent_prompt += f"\n\nExisting references:\n{'\n'.join(['- {}'.format(reference) for reference in self.source_list])}"
            webpage_browse_agent_prompt += f"\n\nWeb search results:\n{web_search_content}"
            webpage_browse_agent_response: RunOutput = await webpage_browse_agent.arun(webpage_browse_agent_prompt)  # type: ignore
            webpage_browse_content = webpage_browse_agent_response.content
            print(f"Webpage browse result:\n{webpage_browse_content}")
            logger.debug(f"self.source_list: {"\n".join([f"[{index + 1}] {source}" for index, source in enumerate(self.source_list)])}")

            if not isinstance(webpage_browse_content, str):
                # TODO: Better error handling
                logger.error("error occured in webpage browse. Exiting.")
                break

            # Summarize
            summary_agent_prompt = f"Research topic: {self.research_topic}"
            summary_agent_prompt += f"\n\nReferences:\n{'\n'.join(['- {}'.format(reference) for reference in self.source_list])}"
            summary_agent_prompt += f"\n\nCurrent summary:\n\n{self.summary}"
            summary_agent_response: RunOutput = await summary_agent.arun(summary_agent_prompt)  # type: ignore
            summary_agent_content = summary_agent_response.content

            if not isinstance(summary_agent_content, str):
                # TODO: Better error handling
                logger.error("Error occured in summarization. Exiting.")
                break

            # Update summary
            self.summary = summary_agent_content
            self.num_turns += 1

            # Debug
            print(f"[DEBUG] Turn {self.num_turns} summary:")
            print(self.summary + "\n")

            # At the end of the loop, evaluate whether research is sufficient
            # TODO: Better evaluation criteria
            # Hard requirement: At least 5 sources token into consideration
            if len(self.source_list) >= 5:
                print("[DEBUG] Report has used 5 sources, ending the research process.")
                break
