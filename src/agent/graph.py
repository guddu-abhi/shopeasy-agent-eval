"""LangGraph ReAct agent for e-commerce customer support."""

from __future__ import annotations

from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama

from src.agent.tools import ALL_TOOLS
from src.agent.prompts import SYSTEM_PROMPT

DEFAULT_MODEL = "qwen2.5:3b"


def build_graph(model_name: str = DEFAULT_MODEL):
    """Build and return the LangGraph ReAct agent graph."""
    llm = ChatOllama(model=model_name)
    graph = create_react_agent(llm, ALL_TOOLS, prompt=SYSTEM_PROMPT)
    return graph
