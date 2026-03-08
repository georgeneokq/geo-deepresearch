from typing import Dict
from geo_deepresearch.subagents.agent_runner import AgentRunner

class CtiAgentRunner(AgentRunner):
    def __init__(self):
        super().__init__()
    
    def source_limit(self) -> int:
        # TODO: Increase as CTI requires more browsing. Currently lowered for testing
        return 5
    
    def priority_sources(self) -> Dict[str, str]:
        return {
            "IOCs": "cloud.google.com"
        }
