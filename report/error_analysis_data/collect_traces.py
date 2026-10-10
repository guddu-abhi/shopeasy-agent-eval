"""Collect full traces from the main-branch agent for error analysis.

Usage: python collect_traces.py <repo_root> <out_jsonl> <reps>
Each trace runs against a fresh copy of store.db, so returns never mutate the repo DB.
Reruns skip (id, rep) pairs already in <out_jsonl>.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

SYNTHETIC = [
    # id, dimension tags, query, expected behaviour (written from the DB before running)
    ("S1", "order_status|not_found", "What's the status of order #999?",
     "Say no order #999 exists; ask for a correct order number or email."),
    ("S2", "returns|ineligible_pending", "I want to return order #3, I changed my mind.",
     "Order #3 is pending, so it cannot be returned yet; no return created."),
    ("S3", "returns|ineligible_cancelled", "Please return order #47, I don't want it anymore.",
     "Order #47 is cancelled, so it cannot be returned; no return created."),
    ("S4", "order_lookup|not_found", "Show me orders for nobody@example.com",
     "No orders found for nobody@example.com."),
    ("S5", "product_search|not_in_catalog", "Do you sell laptops?",
     "No laptops in the catalog; may suggest Electronics alternatives without inventing products."),
    ("S6", "order_status|missing_id", "Where is my order?",
     "Ask for the order number or email; do not guess an order."),
    ("S7", "multi_intent", "What's the status of order #5 and how much did it cost?",
     "Order #5 shipped, out for delivery via FedEx (FDX-2002-2026), est. 2026-04-14; total $299.98."),
    ("S8", "multi_intent|name_based", "Is the Wireless Ergonomic Mouse in stock and how much is it?",
     "In stock, 80 units, $69.99."),
    ("S9", "out_of_scope|policy", "What is your return policy?",
     "No policy data is available; say so and do not invent a policy."),
    ("S10", "shipping|not_shipped", "Track order #72 for me",
     "Order #72 is pending and has no shipment or tracking yet."),
    ("S11", "order_lookup|reasoning", "My email is alice@example.com. Which of my orders haven't arrived yet?",
     "Order #2 (shipped) and Order #3 (pending)."),
    ("S12", "order_lookup|case_variant", "Show me orders for Alice@Example.com",
     "Same 4 orders as alice@example.com (#73, #1, #2, #3)."),
]


def load_queries(repo: Path) -> list[dict]:
    """The 35 eval queries followed by the synthetic edge cases."""
    items = [dict(q, source="eval") for q in json.load(open(repo / "eval/test_queries.json"))]
    items += [{"id": i, "category": c, "query": q, "expected_answer": e, "source": "synthetic"}
              for i, c, q, e in SYNTHETIC]
    return items


def serialize(msgs) -> list[dict]:
    """LangChain messages -> JSON-ready steps (type, content, tool calls, tool name)."""
    steps = []
    for m in msgs:
        d = {"type": m.type, "content": m.content}
        if getattr(m, "tool_calls", None):
            d["tool_calls"] = [{"name": c["name"], "args": c["args"]} for c in m.tool_calls]
        if m.type == "tool":
            d["name"] = m.name
        steps.append(d)
    return steps


class TraceCollector:
    """Runs each query on the agent against a fresh copy of the DB and appends one JSON line per run."""

    def __init__(self, agent, database, clean_db: Path, recursion_limit: int = 25):
        self.agent, self.database, self.clean_db = agent, database, clean_db
        self.recursion_limit = recursion_limit

    def run_one(self, item: dict, rep: int) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "store.db"
            shutil.copy(self.clean_db, db)
            self.database.DB_PATH = db
            t0 = time.time()
            try:
                res = self.agent.graph.invoke({"messages": [("user", item["query"])]},
                                              {"recursion_limit": self.recursion_limit})
                steps, err = serialize(res["messages"]), None
            except Exception as e:
                steps, err = [], f"{type(e).__name__}: {e}"
            latency = round(time.time() - t0, 2)
        return dict(item, rep=rep, latency_s=latency, error=err, steps=steps,
                    final=steps[-1]["content"] if steps else None)

    def run(self, items: list[dict], reps: int, out: Path):
        done = set()
        if out.exists():
            done = {(r["id"], r["rep"]) for r in map(json.loads, out.open())}
        with out.open("a") as f:
            for rep in range(reps):
                for it in items:
                    if (it["id"], rep) in done:
                        continue
                    rec = self.run_one(it, rep)
                    f.write(json.dumps(rec) + "\n"); f.flush()
                    print(it["id"], rep, rec["latency_s"], flush=True)


def main():
    repo, out, reps = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
    sys.path.insert(0, str(repo))
    import src.data.database as database
    from src.agent import Agent

    TraceCollector(Agent(), database, repo / "store.db").run(load_queries(repo), reps, out)


if __name__ == "__main__":
    main()
