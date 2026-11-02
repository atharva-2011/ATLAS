"""Registry and dispatch factory for specialized research agents."""

from agent_runtime.agents.base import BaseSpecializedAgent
from agent_runtime.agents.critic import CriticAgent
from agent_runtime.agents.document_researcher import DocumentResearcherAgent
from agent_runtime.agents.planner import PlannerAgent
from agent_runtime.agents.synthesizer import SynthesizerAgent
from agent_runtime.agents.verifier import EvidenceVerifierAgent
from agent_runtime.agents.web_researcher import WebResearcherAgent
from agent_runtime.llm.base import BaseLLMProvider


class AgentRegistry:
    """Instantiates and caches configured specialized agents."""

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        retrieval_service_url: str = "http://127.0.0.1:8003",
    ) -> None:
        self.llm_provider = llm_provider
        self.retrieval_service_url = retrieval_service_url
        self._agents: dict[str, BaseSpecializedAgent] = {
            "planner": PlannerAgent(llm_provider),
            "document_researcher": DocumentResearcherAgent(
                llm_provider=llm_provider,
                retrieval_service_url=retrieval_service_url,
            ),
            "web_researcher": WebResearcherAgent(llm_provider),
            "evidence_verifier": EvidenceVerifierAgent(llm_provider),
            "critic": CriticAgent(llm_provider),
            "synthesizer": SynthesizerAgent(llm_provider),
        }

    def get_agent(self, agent_type: str) -> BaseSpecializedAgent:
        """Retrieve specialized agent by its registered type identifier."""
        norm = agent_type.lower().strip()
        if norm not in self._agents:
            raise KeyError(
                f"Unknown agent type '{agent_type}'. Available: {list(self._agents.keys())}"
            )
        return self._agents[norm]

    def list_available_agents(self) -> list[str]:
        return list(self._agents.keys())
