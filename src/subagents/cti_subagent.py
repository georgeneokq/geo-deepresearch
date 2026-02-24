import json
import os
import httpx
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.models.openai import OpenAILike
from agno.tools.websearch import WebSearchTools
from agno.tools.jina import JinaReaderTools
from util.tokens import count_tokens
from tools.time import get_current_datetime

# Default 100k max tokens
MODEL_MAX_TOKENS = int(os.environ.get("DEEP_RESEARCH_MODEL_MAX_TOKENS", 100000))

research_agent_instructions = """
You are an expert in CTI, Cyber Threat Intelligence deep research.
You will be given a query related to CTI, along with a summary of the findings so far.
Given the web search and webpage browsing tools, gather information on the query.
Once you browse a webpage with useful information, you must respond with an updated summary of the findings.
Add on to the summary given to you by the user, but deduplicate information as necessary.
All statements in your answer must be linked to a citation.
Before you browse a webpage, ensure it is not in the list of already browsed webpages.

---

Prioritize sources:
- Google cloud: https://cloud.google.com

---

Refer to example response below, but be more detailed where necessary.

---

IOCs found:
- www.badsite.com [1]
- 162.108.0.2 [2]

References:
1. https://cloud.google.com/blog/topics/...
2. https://www.citation2.com
""".strip()


# TODO: Abstract common logic into abstract class
class CtiAgentRunner:
    source_list: list[str]
    current_token_usage: int
    remaining_token_count: int
    num_turns: int
    query: str
    summary: str
    jina_api_key: str
    jina_timeout: int | None
    agent: Agent

    def __init__(self):
        self.source_list = []
        self.current_token_usage = 0
        self.remaining_token_count = 0
        self.num_turns = 0
        self.query = ""
        self.summary = "No research done yet"
        self.jina_api_key = os.environ.get("JINA_API_KEY", "")
        jina_timeout = os.environ.get("JINA_TIMEOUT")
        self.jina_timeout = int(jina_timeout) if jina_timeout else None
        self.agent = self.create_agent()
    
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
Estimated word count limit: {recommended_word_limit}.
Use the word count limit as a guideline on how concise you must be.
        """.strip()

        summarizer_agent = Agent(
            model=OpenAILike(
                id=os.environ.get("DEEP_RESEARCH_MODEL", "z-ai/glm-4.7-flash"),
                base_url=os.environ.get("DEEP_RESEARCH_BASE_URL"),
                api_key=os.environ.get("DEEP_RESEARCH_API_KEY"),
                temperature=0.6,
                max_tokens=max_tokens
            ),
            instructions=summarizer_instructions,
        )

        user_prompt = f"Query: {self.query}\n\nWebpage contents:\n{contents}"
        result: RunOutput = await summarizer_agent.arun(user_prompt)  # type:ignore

        if not isinstance(result.content, str):
            raise RuntimeError(f"Unexpected output from summarizer agent while processing \"{self.query}\".")
        
        return result.content


    async def web_search(self, query: str):
        """
        Currently not in use. Agents use Agno's WebSearchTools toolkit for now
        """
        # Serper
        pass

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
            print(f"[DEBUG] Jina data:\n{json.dumps(jina_data, indent=2)}")
            raw_webpage_content = jina_data.get("content", "")
            
            # --- START: RAG-Inspired Semantic Chunking ---
            incoming_tokens = count_tokens(raw_webpage_content)
            
            if incoming_tokens > 10000:
                print(f"[DEBUG] Megapage detected ({incoming_tokens} tokens). Processing in chunks...")
                # We use overlap so the model doesn't lose context between chunks
                chunks = self._semantic_chunker(raw_webpage_content, max_tokens=7000, overlap=500)
                
                intermediate_summaries = []
                for i, chunk in enumerate(chunks):
                    print(f"[DEBUG] Processing chunk {i+1}/{len(chunks)}...")
                    # Each chunk gets a fixed budget for its mini-summary
                    chunk_sum = await self.summarize_webpage(chunk, 800)
                    intermediate_summaries.append(chunk_sum)
                
                # Consolidate: This becomes the new input for the final update
                raw_webpage_content = "\n\n--- NEXT SECTION ---\n\n".join(intermediate_summaries)
            # --- END: Chunking ---

            # Your updated Budgeting Logic
            MIN_SUMMARY_ROOM = 150 
            buffer_tokens = self._word_count_to_token_count(200)
            current_summary_size = count_tokens(self.summary) if self.summary else 0

            if self.num_turns == 0:
                # 3/4 of remaining token count
                summarize_max_tokens = int(self.remaining_token_count / 4 * 3)
            else:
                available_space = self.remaining_token_count - current_summary_size - buffer_tokens
                summarize_max_tokens = max(available_space, MIN_SUMMARY_ROOM)

            print(f"[DEBUG] Budgeting {summarize_max_tokens} tokens for this summary.")
            summarized = await self.summarize_webpage(raw_webpage_content, summarize_max_tokens)
            
            self.source_list.append(url)
            return summarized

        except Exception as e:
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
            start += (words_per_chunk - overlap_words)
            
            # Safety break to avoid infinite loops
            if start >= len(words) or words_per_chunk <= overlap_words:
                break
                
        return chunks

    def create_agent(self):
        """
        Spawns a subagent with expertise in Cyber Threat Intelligence deep research.
        """
        cti_subagent = Agent(
            model=OpenAILike(
                id=os.environ.get("DEEP_RESEARCH_MODEL", "z-ai/glm-4.7-flash"),
                base_url=os.environ.get("DEEP_RESEARCH_BASE_URL"),
                api_key=os.environ.get("DEEP_RESEARCH_API_KEY"),
                temperature=0.8
            ),
            instructions=research_agent_instructions,
            tools=[
                WebSearchTools(backend="google"),
                self.webpage_browse,
            ]
        )
        return cti_subagent
    
    def reset_state(self):
        self.__init__()

    async def run(self, query: str):
        """
        Asynchronously runs agent in a loop.
        Context is cleared at the end of each turn.
        """
        self.query = query

        print(f"[DEBUG] Processing query: {self.query}")

        # Loop: Browse Webpage -> Update summary of findings -> Evaluate whether research is sufficient
        while True:
            context = f"""
Query: {self.query}

---

Summary of findings so far:

{self.summary}

---

List of sources browsed:

{"\n".join([f"[{index + 1}] {source}" for index, source in enumerate(self.source_list)])}

---

Current datetime:
{get_current_datetime()}
""".strip()

            # Remaining token count for current turn
            self.remaining_token_count = MODEL_MAX_TOKENS - count_tokens(context)

            print(f"[DEBUG] Remaining tokens for current turn: {self.remaining_token_count}")
            
            # Get a summary
            response: RunOutput = await self.agent.arun(context)  # type: ignore

            summary = response.content
            
            # It should be a string. Just for type hinting and unexpected errors
            if not isinstance(summary, str):
                continue

            # Update summary
            self.summary = summary
            self.num_turns += 1

            # Debug
            print(f"[DEBUG] Turn {self.num_turns} summary:")
            print(self.summary + "\n")

            # At the end of the loop, evaluate whether research is sufficient
            # TODO: Better evaluation criteria
            # Hard requirement: At least 5 sources token into consideration
            if len(self.source_list) >= 5:
                break
