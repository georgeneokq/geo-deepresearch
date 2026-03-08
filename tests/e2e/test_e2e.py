import pytest
from langfuse import observe
from geo_deepresearch.util.logging import setup_logging, get_logger
from geo_deepresearch.decompose import DecomposerOutputItem
from geo_deepresearch.subagents import create_research_subagent, AgentRunner, run_agents
from geo_deepresearch.summarize import summarize_for_final_report
from geo_deepresearch.util.testing import extract_citation_count


@pytest.mark.e2e
@pytest.mark.asyncio
@observe(name="Test: Two CTI Subagents")
async def test_two_cti_subagents():
    setup_logging()

    logger = get_logger(__name__)
    logger.setLevel("DEBUG")

    # Prepare LLM for free-form content judging
    research_topic = "IOCs of APT42"

    agents: list[AgentRunner] = []

    subqueries: list[DecomposerOutputItem] = [
        DecomposerOutputItem(expertise="cti", query="IOCs of APT42"),
        DecomposerOutputItem(expertise="cti", query="Past Incidents of APT42"),
    ]

    # Create agents
    for subquery in subqueries:
        agents.append(create_research_subagent(expertise=subquery.expertise))

    # Run agents
    queries = [subquery.query for subquery in subqueries]
    results = await run_agents(queries, agents, min_sources=1)

    # Check if both research agents return without exception
    assert len(results) == 2

    subqueries_str = [subquery.query for subquery in subqueries]
    final_summary = await summarize_for_final_report(
        research_topic, subqueries_str, results
    )

    # Add up the total number of sources that should be in the report.
    # Deduplicate as we expect the sources to be merged by the summarizer.
    citation_set = { source for agent in agents for source in agent.source_list }
    for agent in agents:
        for source in agent.source_list:
            citation_set.add(source)

    expected_citation_count = len(citation_set)

    citation_count = await extract_citation_count(final_summary)

    assert citation_count == expected_citation_count
