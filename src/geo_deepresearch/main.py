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

import asyncio
from types import CoroutineType
from typing import Any
from langfuse import observe
from pydantic import BaseModel
from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
from geo_deepresearch.util.logging import setup_logging
from geo_deepresearch.subagents import get_subagent_by_category
from geo_deepresearch.subagents.cti_subagent import CtiAgentRunner
from geo_deepresearch.subagents.general_subagent import GeneralAgentRunner
from geo_deepresearch.util.logging import get_logger
from geo_deepresearch.util.llm import openai_client, openai_default_model
from geo_deepresearch.decompose import decompose_query
from geo_deepresearch.tokenize import preload_tokenizer

setup_logging()

logger = get_logger()

class ResearchRequestBody(BaseModel):
    query: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    preload_tokenizer()
    yield


app = FastAPI(lifespan=lifespan)

def spawn_research_subagent(expertise: str, query: str) -> CoroutineType[Any, Any, Any]:
    """
    Spawns a subagent.
    """
    # TODO: Create configuration mapping
    agent_runner = get_subagent_by_category(expertise)

    return agent_runner.run(query)


@app.post("/research")
@observe(name="Research")
async def research(body: ResearchRequestBody):
    query = body.query

    running_agents = []

    decomposer_result = await decompose_query(
        openai_client, openai_default_model, query
    )
    subqueries = decomposer_result.subqueries

    # Spawn the agents here
    for subquery in subqueries:
        running_agents.append(
            spawn_research_subagent(expertise=subquery.expertise, query=subquery.query)
        )

    # Wait for subagents to run finish
    summaries = await asyncio.gather(*running_agents)

    # TODO: Agent to analyze all answers from subagents, combine contents and citation list with deduplication
