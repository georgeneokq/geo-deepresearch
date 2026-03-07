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
from langfuse import observe
from openai import AsyncOpenAI
from pydantic import BaseModel
from fastapi import FastAPI
from pydantic import BaseModel
from agno.run.agent import RunOutput
from contextlib import asynccontextmanager
from geo_deepresearch.util.logging import setup_logging
from geo_deepresearch.subagents.cti_subagent import CtiAgentRunner
from geo_deepresearch.util.logging import get_logger
from geo_deepresearch.util.llm import call_llm, openai_client, openai_default_model

setup_logging()

logger = get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    preload_tokenizer()
    yield


app = FastAPI(lifespan=lifespan)

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
- general (anything that doesn't fall into the rest of the categories)

Output format is a JSON object in the following format:
{
  "subqueries": [{"expertise": "cti", "query": "IOCs of APT42"}, {"expertise": "cti", "query": "APT42 past incidents"}]
}

""".strip()

# Coroutines to be awaited later using asyncio.gather

def spawn_research_subagent(expertise: str, query: str):
    if expertise == "cti":
        agent_runner = CtiAgentRunner()
        return agent_runner.run(query)
    elif expertise == "finance":
        # TODO
        pass
    else:
        # Implement a general research agent
        pass


class DecomposerOutputItem(BaseModel):
    expertise: str
    query: str


class DecomposerOutput(BaseModel):
    subqueries: list[DecomposerOutputItem]

async def decompose_query(client: AsyncOpenAI, model: str, query: str) -> DecomposerOutput:
    message = await call_llm(client, model, decomposer_instructions, query, temperature=0.2, output_schema=DecomposerOutput)
    parsed_response = message.parsed
    assert isinstance(parsed_response, DecomposerOutput)
    return parsed_response


def preload_tokenizer():
    from geo_deepresearch.tokenizer_manager import get_tokenizer

    tokenizer_dir = os.environ.get("TOKENIZER_DIR", "../tokenizer")
    logger.info(f"Preloading tokenizer from {tokenizer_dir}...")
    get_tokenizer(os.environ.get("TOKENIZER_DIR", "../tokenizer"))


class ResearchRequestBody(BaseModel):
    query: str


@app.post("/research")
@observe()
async def research(body: ResearchRequestBody):
    query = body.query

    running_agents = []

    decomposer_result = await decompose_query(openai_client, openai_default_model, query)
    subqueries = decomposer_result.subqueries

    # Spawn the agents here
    for subquery in subqueries:
        running_agents.append(spawn_research_subagent(expertise=subquery.expertise, query=subquery.query))

    # Wait for subagents to run finish
    summaries = await asyncio.gather(*running_agents)

    # TODO: Agent to analyze all answers from subagents, combine contents and citation list with deduplication
