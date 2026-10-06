"""E-commerce customer support agent — callable interface."""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from src.agent.graph import build_graph, DEFAULT_MODEL


class Agent:
    """Thin wrapper around the LangGraph agent for easy invocation."""

    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.graph = build_graph(model_name)

    def run(self, message: str) -> str:
        """Send a user message and return the agent's final text response."""
        result = self.graph.invoke(
            {"messages": [HumanMessage(content=message)]}
        )
        return result["messages"][-1].content
