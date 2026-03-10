import asyncio
from typing import Optional
from geo_deepresearch.subagents.agent_runner import AgentRunner
from geo_deepresearch.subagents.general_subagent import GeneralAgentRunner
from geo_deepresearch.subagents.cti_subagent import CtiAgentRunner

# TODO: Updating this list currently requires listing them in decomposer system prompt at `decompose.py`.
#       Better way is to inject dynamically into system prompt to prevent updating two places.
subagent_category_mapping = {
    "cti": CtiAgentRunner,
}


def get_subagent_by_category(category: str) -> AgentRunner:
    agent_runner = subagent_category_mapping.get(category.lower(), GeneralAgentRunner)
    return agent_runner()


def create_research_subagent(expertise: str) -> AgentRunner:
    """
    Spawns a subagent.
    """
    # TODO: Create configuration mapping
    agent_runner = get_subagent_by_category(expertise)

    return agent_runner


async def run_agents(
    queries: list[str],
    agents: list[AgentRunner],
    min_sources: Optional[int] = None,
    parallel_mode: Optional[bool] = False,
):
    if parallel_mode:
        return await asyncio.gather(
            *[agent.run(query, min_sources) for query, agent in zip(queries, agents)]
        )
    else:
        results = []
        for query, agent in zip(queries, agents):
            # Usually would want to disable parallel mode unless we have paid tier for 
            # TODO: Separate parallel mode config for browse, search.
            results.append(await agent.run(query, min_sources))
        return results
