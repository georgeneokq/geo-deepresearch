from geo_deepresearch.subagents.base import AgentRunner
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
