from typing import Dict
from geo_deepresearch.subagents.base import AgentRunner

class GeneralAgentRunner(AgentRunner):
    def __init__(self):
        super().__init__()

    def source_limit(self):
        return 8
    
    def priority_sources(self) -> Dict[str, str]:
        return {}
