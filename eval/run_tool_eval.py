"""Tool-call evaluation runner.

One ToolCallBenchmark per agent tool. Each benchmark holds examples; each example
is a set of paraphrased questions that share one expected answer. For every
example, the runner picks a random paraphrase, sends it to the agent, and scores
the final answer with the benchmark's scorer.

Every agent call runs against a fresh copy of store.db, because initiate_return
writes to the database.

Usage:
    python -m eval.run_tool_eval                      # 1 run per example
    python -m eval.run_tool_eval --runs 3 --seed 7    # 3 random paraphrases per example
    python -m eval.run_tool_eval --benchmark check_inventory
"""

from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from langchain_core.messages import HumanMessage

import src.data.database as database
from src.agent import Agent

EVAL_DATA = Path(__file__).resolve().parent / "test_tool_queries.json"


@dataclass
class ToolCallBenchmark:
    name: str
    examples: list[dict]
    scorer: Callable


# --- Scoring -----------------------------------------------------------------

def _normalize(text: str) -> str:
    text = text.lower().replace("’", "'").replace("‘", "'")
    return text.replace(" & ", " and ")


def _has(term: str, answer: str) -> bool:
    """True if term appears in answer. A number must not be part of a larger
    number, so "60" does not match "$49.60" or "160"."""
    pattern = rf"(?<![\d.]){re.escape(_normalize(term))}(?!\.?\d)"
    return re.search(pattern, _normalize(answer)) is not None


def fraction_present(answer: str, terms: list[str]) -> float:
    return sum(_has(t, answer) for t in terms) / len(terms)


# One scorer per benchmark: (answer, example) -> score in [0, 1].
SCORERS: dict[str, Callable[[str, dict], float]] = {
    # Every in-stock category name appears in the answer.
    "list_categories": lambda answer, ex: fraction_present(answer, ex["must_contain"]),
    # Every matching product name appears.
    "search_products": lambda answer, ex: fraction_present(answer, ex["must_contain"]),
    # The product's name and/or price appear.
    "get_product_details": lambda answer, ex: fraction_present(answer, ex["must_contain"]),
    # The exact stock count appears.
    "check_inventory": lambda answer, ex: fraction_present(answer, ex["must_contain"]),
    # Every item name and the order total appear.
    "lookup_order": lambda answer, ex: fraction_present(answer, ex["must_contain"]),
    # The carrier and tracking number appear.
    "get_shipping_status": lambda answer, ex: fraction_present(answer, ex["must_contain"]),
    # Every order total for the customer appears.
    "search_orders": lambda answer, ex: fraction_present(answer, ex["must_contain"]),
    # The refund amount from the created return appears.
    "initiate_return": lambda answer, ex: fraction_present(answer, ex["must_contain"]),
}


def load_benchmarks() -> list[ToolCallBenchmark]:
    with open(EVAL_DATA) as f:
        entries = json.load(f)

    by_tool: dict[str, list[dict]] = {}
    for entry in entries:
        by_tool.setdefault(entry["tool"], []).append(entry)

    return [
        ToolCallBenchmark(name=tool, examples=examples, scorer=SCORERS[tool])
        for tool, examples in by_tool.items()
    ]


# --- Running -----------------------------------------------------------------

def run_agent(agent: Agent, question: str) -> tuple[str, list[str]]:
    """Return the agent's final answer and the names of the tools it called."""
    result = agent.graph.invoke({"messages": [HumanMessage(content=question)]})
    messages = result["messages"]
    tools_called = [
        call["name"]
        for m in messages
        for call in (getattr(m, "tool_calls", None) or [])
    ]
    return messages[-1].content, tools_called


def run_benchmark(
    bench: ToolCallBenchmark,
    agent: Agent,
    rng: random.Random,
    runs: int,
    scratch_db: Path,
    source_db: Path,
) -> list[dict]:
    results = []
    for ex in bench.examples:
        # Distinct paraphrases while they last, then repeats.
        qs = ex["questions"]
        picks = rng.sample(qs, min(runs, len(qs))) + rng.choices(qs, k=max(0, runs - len(qs)))
        for question in picks:
            shutil.copy(source_db, scratch_db)
            try:
                answer, tools_called = run_agent(agent, question)
            except Exception as e:
                answer, tools_called = f"ERROR: {e}", []

            score = bench.scorer(answer, ex)
            results.append({
                "id": ex["id"],
                "question": question,
                "answer": answer,
                "tools_called": tools_called,
                "tool_hit": bench.name in tools_called,
                "score": score,
            })

            mark = "PASS" if score == 1 else f"{score:.2f}"
            print(f"\n[{bench.name} #{ex['id']}] {mark}  tools={tools_called}")
            print(f"  Q:        {question}")
            print(f"  Expected: {ex['expected_answer']}")
            print(f"  Actual:   {answer.strip() or '<empty reply>'}")
    return results


def print_summary(all_results: dict[str, list[dict]]) -> None:
    print("\n" + "=" * 80)
    print(f"{'Benchmark':<22}{'Runs':>6}{'Score':>8}{'Pass':>8}{'Tool hit':>10}{'Empty':>7}")
    print("-" * 80)
    totals = {"n": 0, "score": 0.0, "pass": 0, "hit": 0, "empty": 0}
    for name, results in all_results.items():
        n = len(results)
        score = sum(r["score"] for r in results)
        passed = sum(r["score"] == 1 for r in results)
        hit = sum(r["tool_hit"] for r in results)
        empty = sum(not r["answer"].strip() for r in results)
        print(f"{name:<22}{n:>6}{score / n:>8.0%}{passed:>5}/{n:<2}{hit:>7}/{n:<2}{empty:>7}")
        for key, val in zip(totals, (n, score, passed, hit, empty)):
            totals[key] += val
    n = totals["n"]
    print("-" * 80)
    print(
        f"{'TOTAL':<22}{n:>6}{totals['score'] / n:>8.0%}{totals['pass']:>5}/{n:<2}"
        f"{totals['hit']:>7}/{n:<2}{totals['empty']:>7}"
    )
    print("\nScore = mean fraction of expected facts found. Pass = all facts found.")
    print("Tool hit = the benchmark's tool was called at least once.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", type=int, default=1, help="random paraphrases per example")
    parser.add_argument("--seed", type=int, default=0, help="seed for paraphrase choice")
    parser.add_argument("--benchmark", action="append", help="run only this benchmark (repeatable)")
    parser.add_argument("--out", type=Path, help="write per-run results to this JSON file")
    args = parser.parse_args()

    benchmarks = load_benchmarks()
    if args.benchmark:
        benchmarks = [b for b in benchmarks if b.name in args.benchmark]

    rng = random.Random(args.seed)
    agent = Agent()
    source_db = database.DB_PATH
    all_results: dict[str, list[dict]] = {}

    with tempfile.TemporaryDirectory() as tmp:
        scratch_db = Path(tmp) / "store.db"
        database.DB_PATH = scratch_db  # tools read DB_PATH on every call
        try:
            for bench in benchmarks:
                print(f"\n{'=' * 80}\nBenchmark: {bench.name} ({len(bench.examples)} examples)")
                all_results[bench.name] = run_benchmark(
                    bench, agent, rng, args.runs, scratch_db, source_db
                )
        finally:
            database.DB_PATH = source_db

    print_summary(all_results)
    if args.out:
        args.out.write_text(json.dumps(all_results, indent=2))
        print(f"\nResults written to {args.out}")


if __name__ == "__main__":
    main()
