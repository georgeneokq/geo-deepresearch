"""
Geo DeepResearch

Method:
Decompose query into multiple task, each to be handled by subagent
Each subagent is an expert (finance, cti, etc.) and will gather information from the internet, prioritizing specific sources.
The subagents will also evaluate if the sources are trustable.
They will also merge information accumulatively, extracting information related to the given query and summarizing at each turn.
All subagents will run in parallel for efficiency.
These subagents will update the list of sources browsed to avoid repetition.
At each summarization turn, the list of sources will be appended to the summarization for the subagent's reference.

Important points:
- Every system prompt must have current datetime appended
"""

import os
import asyncio
from agno.agent import Agent
from agno.models.openai import OpenAILike
from pydantic import BaseModel
from subagents.cti_subagent import CtiAgentRunner
from util.logging import setup_logging

setup_logging()

class DecomposerOutputItem(BaseModel):
    expertise: str
    query: str

class DecomposerOutput(BaseModel):
    subqueries: list[DecomposerOutputItem]


decomposer_instructions = """
Role:
You are to decompose query into parts, tagging each part with a category.

Instructions:
You will receive a query to conduct deep research on.
Expect that the query could span multiple topics.
Break the query down enough such that specialized sub-agents can be spawned for each query.
You may create new sub-queries as needed even if not explicitly specified.
For example, if asked to perform analysis of a company's stock, you may choose to spawn not only "finance" subagent for stock price analysis, but also a subagent with expertise "news" to research on macroeconomic news.

Sub-agent expertise list:
- cti (Cyber Threat Intelligence)
- finance (market data, stocks, commodities, cryptocurrency prices)
- news
- others (anything that doesn't fall into the rest of the categories)

Output format is a JSON object in the following format:
{
  "subqueries": [{"expertise": "cti", "query": "IOCs of APT42"}, {"expertise": "news", "query": "APT42 past incidents"}]
}

""".strip()

# Coroutines to be awaited later using asyncio.gather
running_agents = []

def spawn_research_subagent(expertise: str, query: str):
    if expertise == "cti":
        agent_runner = CtiAgentRunner()
        running_agents.append(agent_runner.run(query))
    elif expertise == "finance":
        # TODO
        pass
    elif expertise == "news":
        # TODO
        pass
    else:
        # Implement a general research agent
        pass


def get_decomposer_agent():
    decomposer_model = OpenAILike(
        id=os.environ.get("DEEP_RESEARCH_MODEL", "z-ai/glm-4.7-flash"),
        base_url=os.environ.get("DEEP_RESEARCH_BASE_URL"),
        api_key=os.environ.get("DEEP_RESEARCH_API_KEY"),
        temperature=0.2
    )
    decomposer_agent = Agent(
        name="Decomposer",
        model=decomposer_model,
        instructions=decomposer_instructions,
        output_schema=DecomposerOutput
    )
    return decomposer_agent


def preload_tokenizer():
    from tokenizer_manager import get_tokenizer
    tokenizer_dir = os.environ.get("TOKENIZER_DIR", "../tokenizer")
    print(f"Preloading tokenizer from {tokenizer_dir}...")
    get_tokenizer(os.environ.get("TOKENIZER_DIR", "../tokenizer"))


async def main():
    preload_tokenizer()
    # query = "What are the IOCs of APT42?"
    # decomposer_agent = get_decomposer_agent()
    # decomposer_result: RunOutput = await decomposer_agent.arun(query)  # type: ignore
    # assert isinstance(decomposer_result.content, DecomposerOutput)
    # subqueries = decomposer_result.content.subqueries

    # Spawn the agents here
    # for subquery in subqueries:
        # spawn_research_subagent(expertise=subquery.expertise, query=subquery.query)

    # TODO: Un-hardcode
    spawn_research_subagent(expertise="cti", query="IOCs of APT42 including domains, IP addresses, and file hashes")
    # Wait for subagents to run finish
    await asyncio.gather(*running_agents)

    # TODO: Agent to analyze all answers from subagents, combine contents and citation list with deduplication


if __name__ == "__main__":
    asyncio.run(main())
