"""Fact-based evaluation of the 35 queries in test_queries.json.

Each run sends one query to the agent on a fresh copy of store.db and records
the reply, every tool call (name, args, output), and these binary checks:

- facts:    every key fact from expected_answer appears in the reply. Key facts
            are dollar amounts, tracking numbers, stock counts (inventory only), plus a few
            hand-added phrases (EXTRA_FACTS).
- grounded: every dollar amount, tracking number and stock count in the reply
            also appears in some tool output, so the agent did not invent it.
- nonempty: the reply has text.

A run passes only if all three checks pass. For each missed fact, the runner
also records whether a tool returned it (the reply dropped it) or not (no tool
call surfaced it).

Usage:
    python -m eval.run_fact_eval --runs 3 --out results.json
    python -m eval.run_fact_eval --ids 4 18 23 31
    python -m eval.run_fact_eval --rescore results.json   # re-score saved runs, no LLM
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import tempfile
from collections import defaultdict
from pathlib import Path

from langchain_core.messages import HumanMessage, ToolMessage

import src.data.database as database
from src.agent import Agent
from eval.run_tool_eval import _has

EVAL_DATA = Path(__file__).resolve().parent / "test_queries.json"

MONEY = re.compile(r"\$\d[\d,]*\.\d{2}")
TRACKING = re.compile(r"\b[A-Z]{2,4}-\d{3,6}-\d{4}\b")
STOCK = re.compile(r"\b(\d+)\s+units\b|\bwe have (\d+)\b", re.IGNORECASE)
REPLY_STOCK = re.compile(
    r"\b(\d+)\s+(?:units?|in stock|available|left)\b|\bwe have (\d+)\b", re.IGNORECASE
)

# "Asked-for" criteria: for these queries, the strict key facts include details
# the customer did not ask for (a tracking number for "when will it arrive?",
# prices for "do you sell X?"). Reading the replies showed correct answers
# failing on those details, so this view checks only what the question asks.
# Other queries use their strict key facts. These are proposed criteria for the
# domain expert to confirm.
ASKED_FOR = {
    6: ["FedEx"],                       # carrier and arrival date; no tracking asked
    9: ["shipped"],                     # status only
    12: ["out for delivery"],           # delivered yet? no tracking asked
    13: ["UV Protection Sunglasses"],   # date and items; no price asked
    16: ["UV Protection Sunglasses"],   # do you sell X? no price asked
    22: ["Cookbook: Mediterranean Meals"],
    24: ["Camping Backpack 60L", "Lightweight Hammock", "Solar Lantern", "Insulated Cooler Bag",
         "Trekking Poles", "Portable Camp Stove", "Packable Rain Jacket", "Emergency Survival Kit"],
    25: ["$294.95"],                    # item count and total; no line prices asked
    27: ["Charcoal Face Wash", "SPF 50 Daily Moisturizer", "Vitamin C Brightening Serum",
         "Rose Water Face Mist"],
    29: ["FedEx"],                      # carrier and arrival date; no tracking asked
    32: ["70"],                         # in stock? no price asked
}

# Facts the regexes cannot extract. For these queries, the key point of the
# expected answer is that a return already exists.
EXTRA_FACTS = {18: ["already"], 23: ["already"], 31: ["already"]}


# --- Scoring -----------------------------------------------------------------

def key_facts(entry: dict) -> list[str]:
    text = entry["expected_answer"]
    facts = MONEY.findall(text) + TRACKING.findall(text)
    if entry["category"] == "inventory":
        facts += [a or b for a, b in STOCK.findall(text)]
    facts += EXTRA_FACTS.get(entry["id"], [])
    return list(dict.fromkeys(facts))  # dedupe, keep order


LINE_ITEM = re.compile(r'"quantity": (\d+), "unit_price": "\$(\d+\.\d{2})"')


def ungrounded(answer: str, tool_text: str) -> list[str]:
    """Numbers in the reply that no tool output contains. A line total
    (quantity x unit price from an order) counts as grounded."""
    line_totals = {f"${int(q) * float(p):.2f}" for q, p in LINE_ITEM.findall(tool_text)}
    claims = MONEY.findall(answer) + TRACKING.findall(answer)
    claims += [a or b for a, b in REPLY_STOCK.findall(answer)]
    return [
        c for c in dict.fromkeys(claims)
        if not _has(c, tool_text) and c not in line_totals
    ]


def score(entry: dict, answer: str, calls: list[dict]) -> dict:
    tool_text = "\n".join(c["output"] for c in calls)
    facts = key_facts(entry)
    missed = [f for f in facts if not _has(f, answer)]
    invented = ungrounded(answer, tool_text)
    checks = {
        "facts": not missed,
        "grounded": not invented,
        "nonempty": bool(answer.strip()),
    }
    asked = ASKED_FOR.get(entry["id"], facts) + EXTRA_FACTS.get(entry["id"], [])
    asked_missed = [f for f in dict.fromkeys(asked) if not _has(f, answer)]
    return {
        "asked_missed": asked_missed,
        "pass_asked": not asked_missed and checks["grounded"] and checks["nonempty"],
        "facts": facts,
        "missed": missed,
        "missed_in_tools": [f for f in missed if _has(f, tool_text)],
        "ungrounded": invented,
        "checks": checks,
        "pass": all(checks.values()),
    }


# --- Running -----------------------------------------------------------------

def run_agent(agent: Agent, query: str) -> tuple[str, list[dict]]:
    """Return the final reply and each tool call with its args and output."""
    messages = agent.graph.invoke({"messages": [HumanMessage(content=query)]})["messages"]
    outputs = {m.tool_call_id: str(m.content) for m in messages if isinstance(m, ToolMessage)}
    calls = [
        {"name": c["name"], "args": c["args"], "output": outputs.get(c["id"], "")}
        for m in messages
        for c in (getattr(m, "tool_calls", None) or [])
    ]
    return messages[-1].content, calls


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def print_summary(results: list[dict], runs: int) -> None:
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        by_cat[r["category"]].append(r)

    print("\n" + "=" * 101)
    print(f"{'Category':<16}{'Runs':>5}{'Pass':>9}{'Asked':>9}{'Facts':>9}{'Grounded':>11}"
          f"{'Empty':>7}{'Missed: in tool / not':>26}")
    print("-" * 101)
    for cat, rs in sorted(by_cat.items()):
        n = len(rs)
        passed = sum(r["pass"] for r in rs)
        asked = sum(r["pass_asked"] for r in rs)
        facts_ok = sum(r["checks"]["facts"] for r in rs)
        grounded = sum(r["checks"]["grounded"] for r in rs)
        empty = sum(not r["checks"]["nonempty"] for r in rs)
        in_tool = sum(len(r["missed_in_tools"]) for r in rs)
        not_tool = sum(len(r["missed"]) - len(r["missed_in_tools"]) for r in rs)
        print(f"{cat:<16}{n:>5}{passed:>6}/{n:<2}{asked:>6}/{n:<2}{facts_ok:>6}/{n:<2}{grounded:>8}/{n:<2}"
              f"{empty:>7}{in_tool:>18} / {not_tool:<4}")

    n = len(results)
    passed = sum(r["pass"] for r in results)
    lo, hi = wilson(passed, n)
    per_run = [
        sum(r["pass"] for r in results if r["run"] == i) for i in range(runs)
    ]
    found = sum(len(r["facts"]) - len(r["missed"]) for r in results)
    total = sum(len(r["facts"]) for r in results)
    print("-" * 101)
    print(f"Pass rate: {passed}/{n} ({passed / n:.0%}), 95% CI {lo:.0%}-{hi:.0%}")
    print(f"Passes per run: {per_run} (of {n // runs} queries each)")
    asked = sum(r["pass_asked"] for r in results)
    alo, ahi = wilson(asked, n)
    print(f"Pass rate, asked-for criteria: {asked}/{n} ({asked / n:.0%}), 95% CI {alo:.0%}-{ahi:.0%}")
    print(f"Key facts found: {found}/{total} ({found / total:.0%})")
    print("\nPass = all key facts in the reply, no ungrounded numbers, and a non-empty reply.")
    print("Asked = the same, checking only the facts the question asks for (ASKED_FOR).")
    print("Missed 'in tool' = a tool returned the fact but the reply left it out.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", type=int, default=1, help="runs per query")
    parser.add_argument("--ids", type=int, nargs="+", help="only run these query ids")
    parser.add_argument("--out", type=Path, help="write per-run results to this JSON file")
    parser.add_argument("--quiet", action="store_true", help="print only the summary")
    parser.add_argument("--min-pass", type=float, help="exit with an error if the pass rate is below this")
    parser.add_argument("--rescore", type=Path, help="re-score a saved results file instead of running")
    args = parser.parse_args()

    entries = json.loads(EVAL_DATA.read_text())
    if args.rescore:
        by_id = {e["id"]: e for e in entries}
        results = json.loads(args.rescore.read_text())
        for r in results:
            r.update(score(by_id[r["id"]], r["answer"], r["calls"]))
        print_summary(results, max(r["run"] for r in results) + 1)
        args.rescore.write_text(json.dumps(results, indent=2))
        return

    if args.ids:
        entries = [e for e in entries if e["id"] in args.ids]

    agent = Agent()
    source_db = database.DB_PATH
    results = []

    with tempfile.TemporaryDirectory() as tmp:
        scratch_db = Path(tmp) / "store.db"
        database.DB_PATH = scratch_db  # tools read DB_PATH on every call
        try:
            for run in range(args.runs):
                for entry in entries:
                    shutil.copy(source_db, scratch_db)
                    try:
                        answer, calls = run_agent(agent, entry["query"])
                    except Exception as e:
                        answer, calls = f"ERROR: {e}", []
                    r = {
                        "run": run,
                        "id": entry["id"],
                        "category": entry["category"],
                        "query": entry["query"],
                        "answer": answer,
                        "calls": calls,
                        **score(entry, answer, calls),
                    }
                    results.append(r)
                    if not args.quiet:
                        mark = "PASS" if r["pass"] else "FAIL"
                        tools = [c["name"] for c in calls]
                        print(f"[run {run} #{entry['id']} {entry['category']}] {mark} tools={tools}"
                              f" missed={r['missed']} ungrounded={r['ungrounded']}", flush=True)
        finally:
            database.DB_PATH = source_db

    print_summary(results, args.runs)
    if args.out:
        args.out.write_text(json.dumps(results, indent=2))
        print(f"\nResults written to {args.out}")
    rate = sum(r["pass"] for r in results) / len(results)
    if args.min_pass is not None and rate < args.min_pass:
        raise SystemExit(f"Pass rate {rate:.0%} is below --min-pass {args.min_pass:.0%}")


if __name__ == "__main__":
    main()
