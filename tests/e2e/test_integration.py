import pytest
from pydantic import BaseModel
from geo_deepresearch.util.logging import setup_logging
from geo_deepresearch.decompose import DecomposerOutputItem
from geo_deepresearch.subagents import spawn_research_subagent, AgentRunner, run_agents
from geo_deepresearch.summarize import summarize_for_final_report
from geo_deepresearch.util.llm import (
    call_llm,
    openai_default_client,
    openai_default_model,
)


class CitationCountExtractionResult(BaseModel):
    num_citations: int


@pytest.mark.integration
@pytest.mark.asyncio
async def test_two_cti_subagents():
    setup_logging()

    # Prepare LLM for free-form content judging
    research_topic = "IOCs of APT42"

    agents: list[AgentRunner] = []

    subqueries: list[DecomposerOutputItem] = [
        DecomposerOutputItem(expertise="cti", query="IOCs of APT42"),
        DecomposerOutputItem(expertise="cti", query="Past Incidents of APT42"),
    ]

    # Spawn the agents here
    for subquery in subqueries:
        agents.append(spawn_research_subagent(expertise=subquery.expertise))

    # Summarize reports
    results = await run_agents(research_topic, agents)
    # Check if both research agents return without exception
    assert len(results) == 2

    subqueries_str = [subquery.query for subquery in subqueries]
    final_summary = await summarize_for_final_report(
        research_topic, subqueries_str, results
    )

    # Add up the total number of sources that should be in the report
    expected_citation_count = sum([len(agent.source_list) for agent in agents])

    # LLM to extract out the number of sources referenced inside the final report
    source_count_extraction_prompt = """
Given a report with a citation list, count the total number of citations.
Return only JSON in this format: {"num_citations": 5}
""".strip()

    extraction_result = await call_llm(
        openai_default_client,
        openai_default_model,
        source_count_extraction_prompt,
        final_summary,
        output_schema=CitationCountExtractionResult,
    )

    if not extraction_result:
        # Unexpected; if this happens it is not necessarily program bug
        raise RuntimeError("LLM as a judge for citation counting failed.")

    assert isinstance(extraction_result.parsed, CitationCountExtractionResult)
    assert (
        extraction_result.parsed.num_citations
        and extraction_result.parsed.num_citations == expected_citation_count
    )
