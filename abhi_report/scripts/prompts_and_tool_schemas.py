"""Save what the model receives in each stage: the system prompt, and each tool's
schema as bind_tools sends it (name, description from the docstring, and the
argument names, types and descriptions). The model never sees the tool code.

Usage, from the repository root:
    python abhi_report/scripts/prompts_and_tool_schemas.py <out.json> <stage>=<code dir> [<stage>=<code dir> ...]
For example, with each tag checked out into a worktree:
    python abhi_report/scripts/prompts_and_tool_schemas.py abhi_report/results/prompts_and_tool_schemas.json \
        baseline=/tmp/baseline iteration_1=/tmp/iteration-1 iteration_2=$PWD
"""

from __future__ import annotations

import json
import subprocess
import sys


def one_stage(code_dir: str) -> dict:
    """Import one stage's agent code and return its prompt and tool schemas."""
    sys.path.insert(0, code_dir)
    from langchain_core.utils.function_calling import convert_to_openai_tool

    from src.agent.prompts import SYSTEM_PROMPT
    from src.agent.tools import ALL_TOOLS

    return {
        "system_prompt": SYSTEM_PROMPT,
        "tools": [convert_to_openai_tool(t)["function"] for t in ALL_TOOLS],
    }


def main() -> None:
    if sys.argv[1] == "--one":
        print(json.dumps(one_stage(sys.argv[2])))
        return
    out, stages = sys.argv[1], dict(a.split("=", 1) for a in sys.argv[2:])
    result = {}
    for stage, code_dir in stages.items():
        # A fresh process per stage, because each stage has its own src package.
        proc = subprocess.run([sys.executable, __file__, "--one", code_dir],
                              capture_output=True, text=True, check=True)
        result[stage] = json.loads(proc.stdout)
    with open(out, "w") as f:
        json.dump(result, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"{out}: " + ", ".join(f"{s} ({len(r['tools'])} tools)" for s, r in result.items()))


if __name__ == "__main__":
    main()
