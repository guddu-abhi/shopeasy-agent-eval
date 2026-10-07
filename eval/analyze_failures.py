"""Count failure modes in saved run_fact_eval results.

The codes come from reading the failed baseline and V7 traces by hand (open
coding), then grouping the notes (axial coding). Each failed run gets the code
of its first failing step, in pipeline order, since later errors usually follow
from earlier ones:

  1. empty_reply           no text and no usable tool call
  2. no_tool_call          answered or asked the customer for an ID, without a tool
  3. skipped_write_action  a return request never called initiate_return
  4. guessed_id            passed a numeric product_id for a product the customer named
  5. invented_syntax       passed made-up query syntax ("email:x", "category:y")
  6. data_not_retrieved    a needed fact is in no tool output (wrong tool, wrong
                           category, no match, or the tool never returns it)
  7. dropped_fact          a tool returned the fact but the reply left it out
  8. ungrounded_number     the reply has a number no tool returned

Failures use the asked-for criteria (pass_asked), so details the customer did
not ask for are not counted.

Usage:
    python -m eval.analyze_failures report/results/fact_eval_baseline.json report/results/fact_eval_v8.json
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

from eval.run_tool_eval import _has

CODES = [
    "empty_reply", "no_tool_call", "skipped_write_action", "guessed_id",
    "invented_syntax", "data_not_retrieved", "dropped_fact", "ungrounded_number",
]


def code(r: dict) -> str:
    calls = r["calls"]
    names = [c["name"] for c in calls]
    if not r["answer"].strip():
        return "empty_reply"
    if not calls:
        return "no_tool_call"
    if r["category"] == "returns" and "initiate_return" not in names:
        return "skipped_write_action"
    if not re.search(r"#?\d", r["query"]) and any(
        isinstance(c["args"].get("product_id"), int) for c in calls
    ):
        return "guessed_id"
    if any(":" in str(v) and "@" in str(v) or str(v).startswith("category:")
           for c in calls for v in c["args"].values()):
        return "invented_syntax"
    tool_text = "\n".join(c["output"] for c in calls)
    if r["asked_missed"]:
        if any(not _has(f, tool_text) for f in r["asked_missed"]):
            return "data_not_retrieved"
        return "dropped_fact"
    return "ungrounded_number"


def main() -> None:
    paths = [Path(p) for p in sys.argv[1:]]
    tables = {}
    for p in paths:
        results = json.loads(p.read_text())
        failed = [r for r in results if not r["pass_asked"]]
        tables[p.stem] = (Counter(code(r) for r in failed), len(results), failed)

    width = max(len(p.stem) for p in paths) + 2
    print(f"{'Failure mode':<22}" + "".join(f"{p.stem:>{width}}" for p in paths))
    print("-" * (22 + width * len(paths)))
    for c in CODES:
        print(f"{c:<22}" + "".join(f"{tables[p.stem][0][c]:>{width}}" for p in paths))
    print("-" * (22 + width * len(paths)))
    print(f"{'failed / runs':<22}" + "".join(
        f"{f'{sum(t[0].values())}/{t[1]}':>{width}}" for t in tables.values()))

    for name, (_, _, failed) in tables.items():
        print(f"\n{name}: failed runs by code")
        for r in sorted(failed, key=lambda r: (CODES.index(code(r)), r["id"])):
            calls = ", ".join(f"{c['name']}({json.dumps(c['args'])})" for c in r["calls"]) or "-"
            print(f"  [{code(r)}] #{r['id']} run {r['run']}: {calls} | missed {r['asked_missed']}")


if __name__ == "__main__":
    main()
