"""Multi-turn evaluation: does the agent keep context across turns?

Each scenario is a list of customer turns sent in one conversation (one
thread_id). The session passes if the final reply has every must_contain term,
none of the must_not_contain terms, no ungrounded numbers, and the expected DB
state. Scenario 6 first runs another customer's conversation on a different
thread, then checks that nothing from it leaks into the new one.

--no-memory runs the same turns with a stateless agent (each turn on its own),
which is how the agent ran before session memory was added.

Usage:
    python -m eval.run_multiturn_eval --runs 3 --out results.json
    python -m eval.run_multiturn_eval --runs 3 --no-memory
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import uuid
from pathlib import Path

from langchain_core.messages import HumanMessage, ToolMessage

import src.data.database as database
from src.agent import Agent
from eval.run_fact_eval import ungrounded, wilson
from eval.run_scenario_eval import returns_count
from eval.run_tool_eval import _has

EVAL_DATA = Path(__file__).resolve().parent / "test_multiturn.json"


def run_session(agent: Agent, turns: list[str], thread_id: str) -> tuple[list[str], str]:
    """Send each turn and return the replies and the tool outputs of the last turn."""
    replies, tool_text = [], ""
    for turn in turns:
        config = {"configurable": {"thread_id": thread_id}} if agent.memory else None
        messages = agent.graph.invoke({"messages": [HumanMessage(content=turn)]}, config=config)["messages"]
        # Tool outputs produced since this turn's human message.
        last_human = max(i for i, m in enumerate(messages) if isinstance(m, HumanMessage))
        tool_text = "\n".join(str(m.content) for m in messages[last_human:] if isinstance(m, ToolMessage))
        replies.append(messages[-1].content)
    return replies, tool_text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--no-memory", action="store_true", help="stateless agent, as before memory")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    scenarios = json.loads(EVAL_DATA.read_text())
    agent = Agent(memory=not args.no_memory)
    source_db = database.DB_PATH
    results = []

    with tempfile.TemporaryDirectory() as tmp:
        scratch_db = Path(tmp) / "store.db"
        database.DB_PATH = scratch_db
        try:
            for run in range(args.runs):
                for sc in scenarios:
                    shutil.copy(source_db, scratch_db)
                    if "other_thread" in sc:
                        run_session(agent, sc["other_thread"], str(uuid.uuid4()))
                    replies, tool_text = run_session(agent, sc["turns"], str(uuid.uuid4()))
                    final = replies[-1]
                    checks = {
                        "contains": all(_has(t, final) for t in sc["must_contain"]),
                        "not_contains": not any(_has(t, final) for t in sc.get("must_not_contain", [])),
                        "grounded": not ungrounded(final, tool_text),
                    }
                    if "returns_after" in sc:
                        checks["db_state"] = all(
                            returns_count(scratch_db, int(o)) == n for o, n in sc["returns_after"].items()
                        )
                    r = {"run": run, "id": sc["id"], "name": sc["name"], "turns": sc["turns"],
                         "replies": replies, "checks": checks, "pass": all(checks.values())}
                    results.append(r)
                    failed = [k for k, ok in checks.items() if not ok]
                    print(f"[run {run} #{sc['id']} {sc['name']}] {'PASS' if r['pass'] else 'FAIL'} failed={failed}",
                          flush=True)
        finally:
            database.DB_PATH = source_db

    n = len(results)
    k = sum(r["pass"] for r in results)
    lo, hi = wilson(k, n)
    print(f"\nMemory: {'off' if args.no_memory else 'on'}. Sessions passed: {k}/{n} ({k / n:.0%}), 95% CI {lo:.0%}-{hi:.0%}")
    for sc in scenarios:
        rs = [r for r in results if r["id"] == sc["id"]]
        print(f"  #{sc['id']} {sc['name']:<45}{sum(r['pass'] for r in rs)}/{len(rs)}")
    if args.out:
        args.out.write_text(json.dumps(results, indent=2))
        print(f"\nResults written to {args.out}")


if __name__ == "__main__":
    main()
