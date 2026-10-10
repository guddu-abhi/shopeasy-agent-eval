"""Join the hand labels (label_data.py) with the traces, print the counts used in error_analysis.md,
run the ID-grounding check, and optionally write labels.csv with the ground-truth DB columns.

Usage: python labels.py traces.jsonl [labels.csv] [store.db]
"""
from __future__ import annotations

import csv
import re
import statistics
import sys
from collections import Counter, defaultdict

import label_data
from db_facts import COLUMNS as FACT_COLUMNS, DEFAULT_DB, DbFacts
from trace_store import Trace, TraceKey, TraceStore


class LabelBook:
    """Read access to the hand labels for one trace or query."""

    def __init__(self, data=label_data):
        self.labels, self.secondary, self.false_claims = data.LABELS, data.SECONDARY, data.FALSE_CLAIM
        self.codes, self.stages, self.refs = data.CODES, data.STAGE, data.REF

    def keys(self) -> set[TraceKey]:
        return set(self.labels)

    def code(self, key: TraceKey) -> str | None:
        return self.labels[key][0]

    def note(self, key: TraceKey) -> str:
        return self.labels[key][1]

    def ref(self, qid) -> str:
        return self.refs.get(qid, "order_id")


class LabelTable:
    """One row per trace: trace metadata, its labels and, if given, the DB facts for its query."""

    def __init__(self, store: TraceStore, book: LabelBook, facts: DbFacts | None = None):
        assert store.keys() == book.keys(), store.keys() ^ book.keys()
        self.rows = [self._row(store[k], book, facts) for k in book.labels]

    @staticmethod
    def _row(t: Trace, book: LabelBook, facts: DbFacts | None) -> dict:
        tools = [c.name for c in t.tool_calls]
        code = book.code(t.key)
        row = dict(id=t.id, rep=t.rep, source=t.source, category=t.category, ref=book.ref(t.id),
                   passed=code is None, first_failure=code or "", secondary=book.secondary.get(t.key, ""),
                   false_claim=t.key in book.false_claims, note=book.note(t.key),
                   n_tool_calls=len(tools), tools="|".join(tools), latency_s=t.latency_s, query=t.query)
        if facts:
            row.update(zip(FACT_COLUMNS, facts.for_query(t.id)))
        return row

    def write_csv(self, path: str):
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(self.rows[0]))
            w.writeheader()
            w.writerows(self.rows)


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

    def __init__(self, rows: list[dict], store: TraceStore, book: LabelBook):
        self.rows, self.store, self.book = rows, store, book
        self.fails = [r for r in rows if not r["passed"]]

    @staticmethod
    def rate(rs) -> str:
        n = sum(r["passed"] for r in rs)
        return f"{n}/{len(rs)} ({100 * n / len(rs):.0f}%)"

    @staticmethod
    def pass_share(rs) -> float:
        return sum(r["passed"] for r in rs) / len(rs)

    def print_all(self):
        for section in (self.pass_rates, self.failure_codes, self.stages, self.false_claims, self.by_ref,
                        self.by_category, self.consistency, self.misc, self.id_grounding):
            section()

    def pass_rates(self):
        for src in ("eval", "synthetic"):
            print(src, self.rate([r for r in self.rows if r["source"] == src]))
        print("all", self.rate(self.rows))

    def failure_codes(self):
        print("\nFirst-failure counts (n fails =", len(self.fails), ")")
        for c, n in Counter(r["first_failure"] for r in self.fails).most_common():
            qs = sorted({str(r["id"]) for r in self.fails if r["first_failure"] == c},
                        key=lambda x: (x[0] == "S", len(x), x))
            print(f"  {c} {self.book.codes[c]:<50} {n:>3} ({100 * n / len(self.fails):.0f}% of fails)  "
                  f"queries: {', '.join(qs)}")

    def stages(self):
        print("\nBy stage of first failure")
        for st, n in sorted(Counter(self.book.stages[r["first_failure"]] for r in self.fails).items()):
            print(f"  {st:<32} {n:>3} ({100 * n / len(self.fails):.0f}%)")

    def false_claims(self):
        fc = [r for r in self.rows if r["false_claim"]]
        assert all(not r["passed"] for r in fc)
        print(f"\nFalse claims: {len(fc)}/{len(self.fails)} fails ({100 * len(fc) / len(self.fails):.0f}%)",
              dict(Counter(r["first_failure"] for r in fc)))

    def _print_slices(self, title: str, groups: dict):
        print(f"\n{title}")
        for k, rs in sorted(groups.items(), key=lambda kv: self.pass_share(kv[1])):
            codes = dict(Counter(r["first_failure"] for r in rs if not r["passed"]))
            print(f"  {k:<16} {self.rate(rs)}  codes: {codes}")

    def by_ref(self):
        groups = defaultdict(list)
        for r in self.rows:
            groups[r["ref"]].append(r)
        self._print_slices("By entity reference", groups)

    def by_category(self):
        groups = defaultdict(list)
        for r in self.rows:
            if r["source"] == "eval":
                groups[r["category"]].append(r)
        self._print_slices("By eval category", groups)

    def _per_query(self) -> dict:
        perq = defaultdict(list)
        for r in self.rows:
            perq[r["id"]].append(r["passed"])
        return perq

    def consistency(self):
        perq = self._per_query()
        print("\nConsistency across 3 runs (per query):")
        print("  passes out of 3 -> #queries:", dict(sorted(Counter(sum(v) for v in perq.values()).items())))
        print("  flaky queries:", [q for q, v in perq.items() if 0 < sum(v) < 3])

    def misc(self):
        rows = self.rows
        print("\nZero-tool-call traces:", sum(r["n_tool_calls"] == 0 for r in rows),
              "pass among them:", sum(r["passed"] for r in rows if r["n_tool_calls"] == 0))
        print("Invented IDs seen:", Counter(str(c.args) for t in self.store for c in t.tool_calls
                                           if any(v in (123, 12345, 123456) for v in c.args.values())))
        print("initiate_return calls:", sum("initiate_return" in r["tools"] for r in rows))
        print("latency median/max:", statistics.median(r["latency_s"] for r in rows), max(r["latency_s"] for r in rows))
        print("\nFirst failure prevents the needed data reaching the model (B, C, A, D, E, K):",
              sum(r["first_failure"] in ("B", "C", "A", "D", "E", "K") for r in rows))
        print("Order date called a ship/delivery date (L as first or secondary code):",
              sum("L" in (r["first_failure"], r["secondary"]) for r in rows))
        always = {q: [r["first_failure"] for r in rows if r["id"] == q]
                  for q, v in self._per_query().items() if sum(v) == 0}
        print("Always-fail queries:", len(always), always)
        print("BORDERLINE passes:", sum(r["note"].startswith("BORDERLINE") for r in rows))

    def id_grounding(self):
        id_calls, flagged = IdGroundingCheck().run(self.store)
        a_traces = {k for k in self.book.keys() if self.book.code(k) == "A"}
        print(f"ID-grounding check: {id_calls} ID-argument calls; flags {len(flagged)} traces; "
              f"code-A traces {len(a_traces)}; caught {len(flagged & a_traces)}; "
              f"flagged but not A {len(flagged - a_traces)}")


def main():
    traces_path, csv_path = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None
    db_path = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_DB
    store, book = TraceStore.load(traces_path), LabelBook()
    table = LabelTable(store, book, DbFacts(db_path) if csv_path else None)
    if csv_path:
        table.write_csv(csv_path)
    SummaryReport(table.rows, store, book).print_all()


if __name__ == "__main__":
    main()
