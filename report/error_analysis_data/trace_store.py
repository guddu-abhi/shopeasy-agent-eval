"""Shared trace model and loader for the error-analysis scripts."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

TraceKey = tuple  # (query id, rep); the id is an int for eval queries and a str ("S1") for synthetic ones


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: dict


@dataclass(frozen=True)
class Trace:
    """One agent run on one query, as written by collect_traces.py."""
    id: int | str
    rep: int
    query: str
    expected_answer: str
    category: str
    source: str
    latency_s: float
    error: str | None
    steps: list
    final: str | None

    @classmethod
    def from_dict(cls, d: dict) -> Trace:
        return cls(id=d["id"], rep=d["rep"], query=d["query"], expected_answer=d["expected_answer"],
                   category=d["category"], source=d["source"], latency_s=float(d["latency_s"]),
                   error=d["error"], steps=d["steps"], final=d["final"])

    @property
    def key(self) -> TraceKey:
        return (self.id, self.rep)

    @property
    def tool_calls(self) -> list[ToolCall]:
        return [ToolCall(c["name"], c["args"]) for s in self.steps for c in s.get("tool_calls", [])]


class TraceStore:
    """Traces indexed by (id, rep), in file order."""

    def __init__(self, traces: Iterable[Trace]):
        self._traces = {t.key: t for t in traces}

    @classmethod
    def load(cls, path: str | Path) -> TraceStore:
        with open(path) as f:
            return cls(Trace.from_dict(json.loads(line)) for line in f if line.strip())

    def __getitem__(self, key: TraceKey) -> Trace:
        return self._traces[key]

    def __iter__(self) -> Iterator[Trace]:
        return iter(self._traces.values())

    def __len__(self) -> int:
        return len(self._traces)

    def keys(self) -> set[TraceKey]:
        return set(self._traces)
