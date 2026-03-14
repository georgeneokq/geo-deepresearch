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

from langfuse import observe
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from geo_deepresearch.util.logging import setup_logging
from geo_deepresearch.subagents import create_research_subagent, AgentRunner, run_agents
from geo_deepresearch.util.logging import get_logger
from geo_deepresearch.util.llm import openai_default_client, openai_default_model
from geo_deepresearch.decompose import decompose_query
from geo_deepresearch.tokenize import preload_tokenizer
from geo_deepresearch.summarize import summarize_for_final_report
from geo_deepresearch.subagents.agent_runner import ResearchMode

setup_logging()

logger = get_logger()


class ResearchRequestBody(BaseModel):
    query: str
    mode: str = "hybrid"  # Options: "internet", "internal", "hybrid"


@asynccontextmanager
async def lifespan(app: FastAPI):
    preload_tokenizer()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/research")
@observe(name="Research")
async def research(body: ResearchRequestBody):
    query = body.query
    mode = body.mode

    # Validate and convert mode string to ResearchMode enum
    try:
        research_mode = ResearchMode(mode.lower())
    except ValueError:
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid mode '{mode}'. Must be one of: internet, internal, hybrid"}
        )

    agents: list[AgentRunner] = []

    decomposer_result = await decompose_query(
        openai_default_client, openai_default_model, query
    )
    subqueries = decomposer_result.subqueries

    # Spawn the agents here
    for subquery in subqueries:
        agents.append(create_research_subagent(expertise=subquery.expertise, mode=research_mode))

    # Run the agents. Filter out ones that did not succeed.
    queries = [subquery.query for subquery in subqueries]
    results = await run_agents(queries, agents)

    subqueries_str = [subquery.query for subquery in subqueries]
    final_summary = await summarize_for_final_report(query, subqueries_str, results)

    return JSONResponse(content={"answer": final_summary})
