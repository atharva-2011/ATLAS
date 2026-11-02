"""Base abstract interface and permission contracts for specialized agents."""

from abc import ABC, abstractmethod

from atlas_contracts.agent_schemas import AgentInput, AgentResult


class AgentToolPermission:
    """Explicit tool permissions restricted by agent role."""

    PLANNER_TOOLS = frozenset({"search_index_metadata"})
    DOCUMENT_RESEARCHER_TOOLS = frozenset({"retrieval_service_hybrid_search"})
    WEB_RESEARCHER_TOOLS = frozenset({"web_search", "web_fetch"})
    VERIFIER_TOOLS = frozenset({"citation_match"})
    CRITIC_TOOLS = frozenset({"coverage_audit"})
    SYNTHESIZER_TOOLS = frozenset({"format_report"})


class BaseSpecializedAgent(ABC):
    """Abstract base class for all specialized research agents."""

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Role identifier (e.g., 'planner', 'document_researcher', 'web_researcher')."""
        ...

    @property
    @abstractmethod
    def allowed_tools(self) -> frozenset[str]:
        """Strictly allowed tool names for this agent."""
        ...

    @abstractmethod
    async def run(self, payload: AgentInput) -> AgentResult:
        """Execute agent task and return typed AgentResult with structured output."""
        ...
