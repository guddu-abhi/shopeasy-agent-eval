"""Bare-bones evaluation runner.

Runs each test query through the agent and prints the actual response alongside
the expected answer. 
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from src.agent import Agent

EVAL_DATA = Path(__file__).resolve().parent / "test_queries.json"


def load_queries() -> list[dict]:
    with open(EVAL_DATA) as f:
        return json.load(f)


def main() -> None:
    queries = load_queries()
    agent = Agent()
    n_queries = len(queries)

    print(f"Running {len(queries)} evaluation queries...\n")
    print("=" * 80)

    for i, entry in enumerate(queries):
        qid = entry["id"]
        query = entry["query"]
        expected = entry["expected_answer"]
        category = entry["category"]

        print(f"\n[Query {qid}] {i+1}/{n_queries} ({category})")
        print(f"  Input:    {query}")
        print(f"  Expected: {expected}")

        try:
            actual = agent.run(query)
        except Exception as e:
            actual = f"ERROR: {e}"

        print(f"  Actual:   {actual}")
        print("-" * 80)

    print("\nEvaluation complete.")


if __name__ == "__main__":
    main()
