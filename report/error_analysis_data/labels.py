"""Join the hand labels (label_data.py) with the traces, print the counts used in error_analysis.md,
run the ID-grounding check, and optionally write labels.csv with the ground-truth DB columns.

Usage: python labels.py [--labels MODULE] traces.jsonl [labels.csv] [store.db]
--labels picks the label module (default label_data).
"""
from __future__ import annotations

import csv
import importlib
import re
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass

import label_data
from db_facts import COLUMNS as FACT_COLUMNS, DEFAULT_DB, DbFacts
from trace_store import Trace, TraceKey, TraceStore

BORDERLINE = "BORDERLINE: "  # note prefix for close calls that still pass


@dataclass(frozen=True)
class LabeledTrace:
    """A trace plus its hand labels."""
    trace: Trace
    code: str | None  # first failure; None means pass
    secondary: str
    false_claim: bool
    note: str
    ref: str

    @property
    def passed(self) -> bool:
        return self.code is None

    @property
    def borderline(self) -> bool:
        return self.passed and self.note.startswith(BORDERLINE)

    @property
    def outcome(self) -> str:
        return "fail" if not self.passed else "borderline" if self.borderline else "pass"

    @property
    def failure(self) -> str:
        return "+".join(c for c in (self.code, self.secondary) if c)

    @property
    def reason(self) -> str:
        return self.note.removeprefix(BORDERLINE)


class LabelBook:
    """Read access to the hand labels."""

    def __init__(self, data=label_data):
        self.labels, self.secondary, self.false_claims = data.LABELS, data.SECONDARY, data.FALSE_CLAIM
        self.codes, self.stages, self.refs = data.CODES, data.STAGE, data.REF

    def keys(self) -> set[TraceKey]:
        return set(self.labels)

    def label(self, t: Trace) -> LabeledTrace:
        code, note = self.labels[t.key]
        return LabeledTrace(t, code, self.secondary.get(t.key, ""), t.key in self.false_claims, note,
                            self.refs.get(t.id, "order_id"))


class LabelTable:
    """All labelled traces, in label order; writes labels.csv."""

    def __init__(self, store: TraceStore, book: LabelBook):
        assert store.keys() == book.keys(), store.keys() ^ book.keys()
        self.items = [book.label(store[k]) for k in book.labels]

    @staticmethod
    def csv_row(lt: LabeledTrace, facts: DbFacts) -> dict:
        t = lt.trace
        db_truth, db_query = facts.for_query(t.id)
        return {"id": t.id, "rep": t.rep, "category": t.category, "ref": lt.ref, "query": t.query,
                "tool_calls": " → ".join(str(c) for c in t.tool_calls), "answer": t.final or "",
                FACT_COLUMNS[0]: db_truth, "outcome": lt.outcome, "failure": lt.failure,
                "false_claim": lt.false_claim, "note": lt.reason, FACT_COLUMNS[1]: db_query}

    def write_csv(self, path: str, facts: DbFacts):
        rows = [self.csv_row(lt, facts) for lt in self.items]
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)


class IdGroundingCheck:
    """Proposed code evaluator: every *_id argument must appear in the user message or an earlier tool result."""

    def run(self, store: TraceStore) -> tuple[int, set[TraceKey]]:
        id_calls, flagged = 0, set()
        for t in store:
            seen = t.query
            for s in t.steps[1:]:
                for c in s.get("tool_calls", []):
                    for a, v in c["args"].items():
                        if a.endswith("_id"):
                            id_calls += 1
                            if not re.search(r"(?<!\d)%s(?!\d)" % v, seen):
                                flagged.add(t.key)
                if s["type"] == "tool":
                    seen += " " + s["content"]
        return id_calls, flagged


class SummaryReport:
    """Prints the counts and slices reported in error_analysis.md."""

    def __init__(self, items: list[LabeledTrace], store: TraceStore, book: LabelBook):
        self.items, self.store, self.book = items, store, book
        self.fails = [x for x in items if not x.passed]

    @staticmethod
    def rate(xs) -> str:
        n = sum(x.passed for x in xs)
        return f"{n}/{len(xs)} ({100 * n / len(xs):.0f}%)"

    @staticmethod
    def pass_share(xs) -> float:
        return sum(x.passed for x in xs) / len(xs)

    def print_all(self):
        for section in (self.pass_rates, self.failure_codes, self.stages, self.false_claims, self.by_ref,
                        self.by_category, self.consistency, self.misc, self.id_grounding):
            section()

    def pass_rates(self):
        for src in ("eval", "synthetic"):
            print(src, self.rate([x for x in self.items if x.trace.source == src]))
        print("all", self.rate(self.items))

    def failure_codes(self):
        print("\nFirst-failure counts (n fails =", len(self.fails), ")")
        for c, n in Counter(x.code for x in self.fails).most_common():
            qs = sorted({str(x.trace.id) for x in self.fails if x.code == c},
                        key=lambda q: (q[0] == "S", len(q), q))
            print(f"  {c} {self.book.codes[c]:<50} {n:>3} ({100 * n / len(self.fails):.0f}% of fails)  "
                  f"queries: {', '.join(qs)}")

    def stages(self):
        print("\nBy stage of first failure")
        for st, n in sorted(Counter(self.book.stages[x.code] for x in self.fails).items()):
            print(f"  {st:<32} {n:>3} ({100 * n / len(self.fails):.0f}%)")

    def false_claims(self):
        fc = [x for x in self.items if x.false_claim]
        assert all(not x.passed for x in fc)
        print(f"\nFalse claims: {len(fc)}/{len(self.fails)} fails ({100 * len(fc) / len(self.fails):.0f}%)",
              dict(Counter(x.code for x in fc)))

    def _print_slices(self, title: str, groups: dict):
        print(f"\n{title}")
        for k, xs in sorted(groups.items(), key=lambda kv: self.pass_share(kv[1])):
            codes = dict(Counter(x.code for x in xs if not x.passed))
            print(f"  {k:<16} {self.rate(xs)}  codes: {codes}")

    def by_ref(self):
        groups = defaultdict(list)
        for x in self.items:
            groups[x.ref].append(x)
        self._print_slices("By entity reference", groups)

    def by_category(self):
        groups = defaultdict(list)
        for x in self.items:
            if x.trace.source == "eval":
                groups[x.trace.category].append(x)
        self._print_slices("By eval category", groups)

    def _per_query(self) -> dict:
        perq = defaultdict(list)
        for x in self.items:
            perq[x.trace.id].append(x.passed)
        return perq

    def consistency(self):
        perq = self._per_query()
        print("\nConsistency across 3 runs (per query):")
        print("  passes out of 3 -> #queries:", dict(sorted(Counter(sum(v) for v in perq.values()).items())))
        print("  flaky queries:", [q for q, v in perq.items() if 0 < sum(v) < 3])

    def misc(self):
        items = self.items
        no_calls = [x for x in items if not x.trace.tool_calls]
        print("\nZero-tool-call traces:", len(no_calls), "pass among them:", sum(x.passed for x in no_calls))
        print("Invented IDs seen:", Counter(str(c.args) for t in self.store for c in t.tool_calls
                                           if any(v in (123, 12345, 123456) for v in c.args.values())))
        print("initiate_return calls:", sum(any(c.name == "initiate_return" for c in x.trace.tool_calls) for x in items))
        latencies = [x.trace.latency_s for x in items]
        print("latency median/max:", statistics.median(latencies), max(latencies))
        print("\nFirst failure prevents the needed data reaching the model (B, C, A, D, E, K):",
              sum(x.code in ("B", "C", "A", "D", "E", "K") for x in items))
        print("Order date called a ship/delivery date (L as first or secondary code):",
              sum("L" in (x.code, x.secondary) for x in items))
        always = {q: [x.code for x in items if x.trace.id == q]
                  for q, v in self._per_query().items() if sum(v) == 0}
        print("Always-fail queries:", len(always), always)
        print("BORDERLINE passes:", sum(x.borderline for x in items))

    def id_grounding(self):
        id_calls, flagged = IdGroundingCheck().run(self.store)
        a_traces = {x.trace.key for x in self.items if x.code == "A"}
        print(f"ID-grounding check: {id_calls} ID-argument calls; flags {len(flagged)} traces; "
              f"code-A traces {len(a_traces)}; caught {len(flagged & a_traces)}; "
              f"flagged but not A {len(flagged - a_traces)}")


def main():
    args = sys.argv[1:]
    data = label_data
    if args[:1] == ["--labels"]:  # e.g. --labels label_data_better_tool_docstring
        data = importlib.import_module(args[1])
        args = args[2:]
    traces_path, csv_path = args[0], args[1] if len(args) > 1 else None
    db_path = args[2] if len(args) > 2 else DEFAULT_DB
    store, book = TraceStore.load(traces_path), LabelBook(data)
    table = LabelTable(store, book)
    if csv_path:
        table.write_csv(csv_path, DbFacts(db_path))
    SummaryReport(table.items, store, book).print_all()


if __name__ == "__main__":
    main()
