"""Run the held-out scenario set (test_scenarios.json, built by build_scenarios).

Each run sends one scenario to the agent on a fresh copy of store.db and
applies binary checks:

- contains:  every must_contain term is in the reply.
- any_of:    at least one must_contain_any term is in the reply (used for
             declines, such as an unknown product or a pending order).
- grounded:  no dollar amount, tracking number or stock count in the reply is
             missing from the tool outputs.
- nonempty:  the reply has text.
- db_state:  after the run, each order in returns_after has that many return rows.

A run passes only if every check passes. Results are grouped by each scenario
dimension (intent, ref, state, phrasing).

Usage:
    python -m eval.run_scenario_eval --runs 2 --out results.json
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import tempfile
from collections import defaultdict
from pathlib import Path

import src.data.database as database
from src.agent import Agent
from eval.run_fact_eval import run_agent, ungrounded, wilson
from eval.run_tool_eval import _has

EVAL_DATA = Path(__file__).resolve().parent / "test_scenarios.json"
DIMENSIONS = ["intent", "ref", "state", "phrasing"]


def returns_count(db: Path, order_id: int) -> int:
    conn = sqlite3.connect(db)
    n = conn.execute("SELECT COUNT(*) FROM returns WHERE order_id = ?", (order_id,)).fetchone()[0]
    conn.close()
    return n


def score(sc: dict, answer: str, calls: list[dict], db: Path | None) -> dict:
    tool_text = "\n".join(c["output"] for c in calls)
    missing = [t for t in sc["must_contain"] if not _has(t, answer)]
    invented = ungrounded(answer, tool_text)
    checks = {
        "contains": not missing,
        "any_of": not sc["must_contain_any"] or any(_has(t, answer) for t in sc["must_contain_any"]),
        "grounded": not invented,
        "nonempty": bool(answer.strip()),
    }
    if "returns_after" in sc and db is not None:
        checks["db_state"] = all(
            returns_count(db, int(oid)) == n for oid, n in sc["returns_after"].items()
        )
    return {"missing": missing, "ungrounded": invented, "checks": checks, "pass": all(checks.values())}


def print_summary(results: list[dict]) -> None:
    n = len(results)
    passed = sum(r["pass"] for r in results)
    lo, hi = wilson(passed, n)
    print("\n" + "=" * 72)
    print(f"Pass rate: {passed}/{n} ({passed / n:.0%}), 95% CI {lo:.0%}-{hi:.0%}")

    for dim in DIMENSIONS:
        groups: dict[str, list[dict]] = defaultdict(list)
        for r in results:
            groups[r[dim]].append(r)
        print(f"\nBy {dim}:")
        for key, rs in sorted(groups.items()):
            k = sum(r["pass"] for r in rs)
            print(f"  {key:<16}{k:>4}/{len(rs):<4}")

    print("\nFailed checks:")
    counts: dict[str, int] = defaultdict(int)
    for r in results:
        for name, ok in r["checks"].items():
            counts[name] += not ok
    for name, c in counts.items():
        print(f"  {name:<10}{c}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", type=int, default=1, help="runs per scenario")
    parser.add_argument("--ids", type=int, nargs="+", help="only run these scenario ids")
    parser.add_argument("--out", type=Path, help="write per-run results to this JSON file")
    parser.add_argument("--rescore", type=Path,
                        help="re-score a saved results file with the current checks (keeps db_state)")
    args = parser.parse_args()

    scenarios = json.loads(EVAL_DATA.read_text())
    if args.rescore:
        by_id = {s["id"]: s for s in scenarios}
        results = json.loads(args.rescore.read_text())
        for r in results:
            sc = by_id[r["id"]]
            db_ok = r["checks"].get("db_state")
            r.update({k: sc[k] for k in ("must_contain", "must_contain_any")})
            r.update(score(sc, r["answer"], r["calls"], None))
            if db_ok is not None:
                r["checks"]["db_state"] = db_ok
                r["pass"] = all(r["checks"].values())
        print_summary(results)
        args.rescore.write_text(json.dumps(results, indent=2))
        return
    if args.ids:
        scenarios = [s for s in scenarios if s["id"] in args.ids]

    agent = Agent()
    source_db = database.DB_PATH
    results = []

    with tempfile.TemporaryDirectory() as tmp:
        scratch_db = Path(tmp) / "store.db"
        database.DB_PATH = scratch_db  # tools read DB_PATH on every call
        try:
            for run in range(args.runs):
                for sc in scenarios:
                    shutil.copy(source_db, scratch_db)
                    try:
                        answer, calls = run_agent(agent, sc["query"])
                    except Exception as e:
                        answer, calls = f"ERROR: {e}", []
                    r = {"run": run, **sc, "answer": answer, "calls": calls,
                         **score(sc, answer, calls, scratch_db)}
                    results.append(r)
                    mark = "PASS" if r["pass"] else "FAIL"
                    failed = [k for k, ok in r["checks"].items() if not ok]
                    print(f"[run {run} #{sc['id']} {sc['intent']}/{sc['state']}] {mark}"
                          f" tools={[c['name'] for c in calls]} failed={failed}", flush=True)
        finally:
            database.DB_PATH = source_db

    print_summary(results)
    if args.out:
        args.out.write_text(json.dumps(results, indent=2))
        print(f"\nResults written to {args.out}")


if __name__ == "__main__":
    main()
