"""Compute pass^k and pass@k from saved eval results, with no agent runs.

pass^k (tau-bench): the chance that k independent runs of a query all pass.
pass@k:             the chance that at least one of k runs passes.
Both use the unbiased estimators over n saved runs per query (c of them passed),
averaged over queries:

    pass^k = mean_q C(c, k) / C(n, k)
    pass@k = mean_q 1 - C(n - c, k) / C(n, k)

The 95% intervals come from a bootstrap over queries (runs of a query stay together).

Usage:
    python -m eval.pass_k abhi_report/results/baseline_original_questions.json abhi_report/results/iteration_2_original_questions.json
    python -m eval.pass_k abhi_report/results/iteration_2_heldout_scenarios.json --by phrasing
    python -m eval.pass_k abhi_report/results/iteration_2_original_questions.json --key pass_asked
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from math import comb
from pathlib import Path


class RunResults:
    """Pass/fail counts per query from one results file: {query id: (n runs, c passed)}."""

    def __init__(self, rows: list[dict], key: str = "pass"):
        runs = defaultdict(list)
        for r in rows:
            runs[r["id"]].append(bool(r[key]))
        self.counts = {q: (len(v), sum(v)) for q, v in runs.items()}

    @classmethod
    def load(cls, path: str | Path, key: str = "pass", where: tuple[str, str] | None = None) -> RunResults:
        rows = json.load(open(path))
        if where:
            rows = [r for r in rows if str(r.get(where[0])) == where[1]]
        return cls(rows, key)

    @property
    def min_runs(self) -> int:
        return min(n for n, _ in self.counts.values())


def pass_hat(n: int, c: int, k: int) -> float:
    return comb(c, k) / comb(n, k)


def pass_at(n: int, c: int, k: int) -> float:
    return 1 - comb(n - c, k) / comb(n, k)


class PassK:
    """Estimates a metric (pass_hat or pass_at) over queries, with a bootstrap interval."""

    def __init__(self, samples: int = 2000, seed: int = 0):
        self.samples, self.seed = samples, seed

    def estimate(self, results: RunResults, k: int, metric=pass_hat) -> tuple[float, float, float]:
        per_query = [metric(n, c, k) for n, c in results.counts.values()]
        rng = random.Random(self.seed)
        means = sorted(sum(rng.choices(per_query, k=len(per_query))) / len(per_query)
                       for _ in range(self.samples))
        return (sum(per_query) / len(per_query),
                means[int(0.025 * self.samples)], means[int(0.975 * self.samples) - 1])


def print_table(name: str, results: RunResults, est: PassK):
    print(f"{name}: {len(results.counts)} queries, {results.min_runs} runs each")
    for k in range(1, results.min_runs + 1):
        hat, lo, hi = est.estimate(results, k, pass_hat)
        at = est.estimate(results, k, pass_at)[0]
        print(f"  k={k}  pass^k {hat:6.1%}  (95% CI {lo:.1%}-{hi:.1%})   pass@k {at:6.1%}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="+", help="results JSON files (a list of rows with id and a pass flag)")
    parser.add_argument("--key", default="pass", help="pass flag to read, e.g. pass or pass_asked")
    parser.add_argument("--by", help="also report each value of this row field, e.g. phrasing")
    args = parser.parse_args()

    est = PassK()
    for path in args.files:
        print_table(path, RunResults.load(path, args.key), est)
        if args.by:
            values = sorted({str(r.get(args.by)) for r in json.load(open(path))})
            for v in values:
                print_table(f"  {args.by}={v}", RunResults.load(path, args.key, (args.by, v)), est)
        print()


if __name__ == "__main__":
    main()
