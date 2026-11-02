"""Specialized research agent implementations and registry exports."""

from agent_runtime.agents.base import AgentToolPermission, BaseSpecializedAgent
from agent_runtime.agents.critic import CriticAgent
from agent_runtime.agents.document_researcher import DocumentResearcherAgent
from agent_runtime.agents.planner import PlannerAgent
from agent_runtime.agents.registry import AgentRegistry
from agent_runtime.agents.synthesizer import SynthesizerAgent
from agent_runtime.agents.verifier import EvidenceVerifierAgent
from agent_runtime.agents.web_researcher import WebResearcherAgent, WebSearchAdapter

__all__ = [
    "AgentRegistry",
    "AgentToolPermission",
    "BaseSpecializedAgent",
    "CriticAgent",
    "DocumentResearcherAgent",
    "EvidenceVerifierAgent",
    "PlannerAgent",
    "SynthesizerAgent",
    "WebResearcherAgent",
    "WebSearchAdapter",
]
