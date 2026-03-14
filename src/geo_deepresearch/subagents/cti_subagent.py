from typing import Dict, Optional
from geo_deepresearch.subagents.agent_runner import AgentRunner, ResearchMode
from geo_deepresearch.internal_browse_manager import InternalBrowseManager

class CtiAgentRunner(AgentRunner):
    def __init__(
        self,
        mode: Optional[ResearchMode] = None,
        internal_browse_manager: Optional[InternalBrowseManager] = None
    ):
        super().__init__(mode=mode, internal_browse_manager=internal_browse_manager)

    def source_limit(self) -> int:
        # TODO: Increase as CTI requires more browsing. Currently lowered for testing
        return 5

    def priority_sources(self) -> Dict[str, str]:
        return {
            "IOCs": "cloud.google.com"
        }
