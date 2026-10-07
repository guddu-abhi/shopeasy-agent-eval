"""E-commerce customer support agent — callable interface."""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from src.agent.graph import build_graph, DEFAULT_MODEL


class Agent:
    """Thin wrapper around the LangGraph agent for easy invocation.

    By default each run() is a separate, single-turn conversation. With
    memory=True, runs that share a thread_id form one conversation.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL, memory: bool = False):
        self.memory = memory
        self.graph = build_graph(model_name, memory=memory)

    def run(self, message: str, thread_id: str = "default") -> str:
        """Send a user message and return the agent's final text response."""
        config = {"configurable": {"thread_id": thread_id}} if self.memory else None
        result = self.graph.invoke(
            {"messages": [HumanMessage(content=message)]}, config=config
        )
        return result["messages"][-1].content
