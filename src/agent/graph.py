"""LangGraph ReAct agent for e-commerce customer support."""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama

from src.agent.tools import ALL_TOOLS
from src.agent.prompts import SYSTEM_PROMPT

DEFAULT_MODEL = "qwen2.5:3b"


def build_graph(model_name: str = DEFAULT_MODEL, memory: bool = False):
    """Build and return the LangGraph ReAct agent graph. With memory, the graph
    keeps each conversation's messages per thread_id, so a follow-up turn
    ("it's grace@example.com") sees the earlier turns."""
    llm = ChatOllama(model=model_name)
    checkpointer = MemorySaver() if memory else None
    graph = create_react_agent(llm, ALL_TOOLS, prompt=SYSTEM_PROMPT, checkpointer=checkpointer)
    return graph
