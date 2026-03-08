import pytest
import asyncio
from geo_deepresearch.decompose import DecomposerOutputItem
from geo_deepresearch.subagents import spawn_research_subagent

@pytest.mark.integration
@pytest.mark.asyncio
async def test_two_subagents():
    running_agents: list = []
    subqueries: list[DecomposerOutputItem] = [
        DecomposerOutputItem(expertise="cti", query="IOCs of APT42"),
        DecomposerOutputItem(expertise="cti", query="Past Incidents of APT42")
    ]

    # Spawn the agents here
    for subquery in subqueries:
        running_agents.append(
            spawn_research_subagent(expertise=subquery.expertise, query=subquery.query)
        )

    # Wait for subagents to run finish
    summaries = await asyncio.gather(*running_agents)

    # Spawn agents
    for subquery in subqueries:
        running_agents.append(
            spawn_research_subagent(expertise=subquery.expertise, query=subquery.query)
        )

    # Wait for subagents to run finish
    summaries = await asyncio.gather(*running_agents)