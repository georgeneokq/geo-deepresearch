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
import random
from langfuse import observe
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from geo_deepresearch.util.logging import setup_logging
from geo_deepresearch.subagents import spawn_research_subagent, AgentRunner
from geo_deepresearch.util.logging import get_logger
from geo_deepresearch.util.llm import openai_client, openai_default_model, call_llm
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


@app.post("/research")
@observe(name="Research")
async def research(body: ResearchRequestBody):
    query = body.query

    agents: list[AgentRunner] = []

    decomposer_result = await decompose_query(
        openai_client, openai_default_model, query
    )
    subqueries = decomposer_result.subqueries

    # Spawn the agents here
    for subquery in subqueries:
        agents.append(spawn_research_subagent(expertise=subquery.expertise))

    # Run the agents. Filter out ones that did not succeed.
    summaries = [
        (subquery, result)
        for (subquery, result) in zip(
            subqueries,
            await asyncio.gather(
                *[agent.run(query) for agent in agents], return_exceptions=True
            ),
        )
        if not isinstance(result, Exception)
    ]

    num_summaries = len(summaries)

    # If no summaries after filtering, everything errored.
    if not num_summaries:
        return JSONResponse(
            content={"answer": "Failed to complete research."},
        )
    elif num_summaries == 1:
        # If only one agent was spawned, return that as the result
        subquery, summary = summaries[0]
        return JSONResponse(content={"answer": summary})
    else:
        # Agent to analyze all answers from subagents, combine contents and citation list with deduplication.
        # To prevent context overflow, we pass in 2 summaries at a time, accumulating a main summary
        # and eventually reduce it to a single summary.

        # Use the first item in the array as the start
        first_subquery, first_summary = summaries[0]
        main_summary = f"**Main report empty, starting with sub-report.**\n\n**Sub-report topic: {first_subquery.query}**\n\n{first_summary}"
        for attempt in range(1, len(summaries)):
            (subquery, summary) = summaries[attempt]
            final_summarizer_instructions = f"""
You are a summarizer agent for the following topic: \"{query}\"
You will be given 2 reports to merge - a main report, and a sub-report. Merge the sub-report into the main report.
Re-index all citations. The final output must have a single, continuous numerical reference list (e.g., [1] through [N]) that matches the provided reports.
Ensure the statements are linked to the new citation numbers correctly.
""".strip()
            main_summary_message = f"**Main report**\n\n{main_summary}"
            next_summary_message = f"**Sub-report**\n\n{summary}"
            user_messages = [main_summary_message, next_summary_message]

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    result = await call_llm(
                        openai_client,
                        openai_default_model,
                        final_summarizer_instructions,
                        user_messages,
                    )
                    main_summary = result.content
                    break
                except Exception as e:
                    # Skip current sub-report if failed.
                    logger.warning(f"Attempt {attempt + 1} failed for sub-report {attempt}: {e}")
                    logger.debug("Retrying 1 more time due to summarization failure")

                    if attempt == max_retries - 1:
                        # If we just failed our last attempt, log error
                        logger.error(f"Exhausted all retries for sub-report {attempt}. Skipping.")
                
                # Exponential backoff with a little bit of random jitter (0 to 1000ms)
                wait_time = (2 ** attempt) + random.random()
                
                logger.warning(f"Attempt {attempt + 1} failed. Retrying in {wait_time:.2f}s...")
                await asyncio.sleep(wait_time)

            logger.debug(f"Updated summary:\n{main_summary}")

        return JSONResponse(content={"answer": main_summary})
