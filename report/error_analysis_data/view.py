"""Print traces compactly: query, expected, tool calls (args + truncated result), final answer.
Usage: python view.py traces.jsonl [id ...]  (ids filter; rep filter via REP env var)"""
from __future__ import annotations

import json
import os
import sys

from trace_store import Trace, TraceStore


class TraceViewer:
    """Renders one trace as a short text block; long results and answers are cut."""

    def __init__(self, result_chars: int = 300, mid_chars: int = 200, answer_chars: int = 900):
        self.result_chars, self.mid_chars, self.answer_chars = result_chars, mid_chars, answer_chars

    def render(self, t: Trace) -> str:
        lines = [f"=== [{t.id}] rep={t.rep} {t.category} {t.latency_s}s err={t.error}",
                 f"Q: {t.query}\nE: {t.expected_answer}"]
        for s in t.steps[1:]:
            if s.get("tool_calls"):
                lines += [f"  CALL {c['name']}({json.dumps(c['args'])})" for c in s["tool_calls"]]
            elif s["type"] == "tool":
                lines.append(f"  RESULT {s['name']}: " + s["content"].replace("\n", " | ")[:self.result_chars])
            elif s["type"] == "ai" and s is not t.steps[-1] and s["content"]:
                lines.append(f"  AI-MID: {s['content'][:self.mid_chars]}")
        lines.append(f"A: {(t.final or '').strip()[:self.answer_chars]}\n")
        return "\n".join(lines)


def selected(store: TraceStore, ids: set[str], rep: str | None):
    return [t for t in store if (not ids or str(t.id) in ids) and (rep is None or str(t.rep) == rep)]


def main():
    viewer = TraceViewer()
    for t in selected(TraceStore.load(sys.argv[1]), set(sys.argv[2:]), os.environ.get("REP")):
        print(viewer.render(t))


if __name__ == "__main__":
    main()
