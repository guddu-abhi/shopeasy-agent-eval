# ShopEasy agent: evaluation and improvement deliverables

This folder holds the deliverables for the Coveo agent-optimization challenge. The agent runs on `qwen2.5:3b` (Ollama) with LangGraph. It was measured, diagnosed, and improved in two iterations.

## Start here

| File | What it is |
|---|---|
| [`index.html`](index.html) | The report as an interactive page. Open it in a browser from this folder, so its links to `results/` work. It needs no server. |
| [`REPORT.md`](REPORT.md) | The same report as Markdown. It has the full prompts, every tool definition per stage, and the steps to regenerate the results. |

Both cover the same content: what "good" means for this agent, the baseline error analysis, how each eval works, what changed in each iteration (per tool), the results, and the next steps.

## The three stages

Each stage has a git tag, so its code can be checked out or compared at any time.

| Stage | Git ref | What changed |
|---|---|---|
| Baseline | tag `baseline` (the `main` branch) | The original agent. |
| Iteration 1 | tag `iteration-1` | A new system prompt, tools that answer in one call (`get_product_details` and `check_inventory` accept a name, a new `list_categories`, and `initiate_return` reports an existing return), and session memory. |
| Iteration 2 | tag `iteration-2`, and the `abhi_optimization` branch | Rewritten tool docstrings and argument descriptions. The tool code is the same as in iteration 1. |

Useful commands:

```bash
git diff baseline iteration-1 -- src/agent/tools.py      # iteration 1 tool changes
git diff iteration-1 iteration-2 -- src/agent/tools.py   # iteration 2 docstring changes
git show iteration-2:report/prompt_tuning.md             # the prompt-tuning log behind the probe numbers
```

## Artifacts in `results/`

Each file name starts with its stage: `baseline_`, `iteration_1_` or `iteration_2_`.

| Files | What they hold | Made by |
|---|---|---|
| `*_original_questions.json` | 35 original questions × 3 runs, scored by both scorers (strict and asked-for). | `eval/run_fact_eval.py` |
| `*_heldout_scenarios.json` | 43 held-out scenarios × 2 runs. They were never used for tuning. | `eval/run_scenario_eval.py` |
| `iteration_*_reworded_questions.json` | 16 questions (2 per tool), each in 4 random wordings. | `eval/run_tool_eval.py` |
| `iteration_*_multiturn_with_memory.json`, `iteration_*_multiturn_without_memory.json` | 6 two-turn sessions × 3 runs, with and without session memory. | `eval/run_multiturn_eval.py` |
| `*_traces.jsonl` | 141 full traces per stage (47 inputs × 3 runs): every message, tool call and tool result. | `scripts/collect_traces.py` |
| `*_labels.csv` | Hand labels for those traces: pass or fail, the first failure code, a false-claim flag, and the database truth. | `scripts/labels.py` |
| `iteration_2_json_variant_traces.jsonl`, `iteration_2_json_variant_labels.csv` | A side experiment in which the tools return JSON instead of plain text. | `scripts/collect_traces.py`, `scripts/labels.py` |
| `prompts_and_tool_schemas.json` | What the model receives in each stage: the system prompt and each tool's name, docstring and arguments. | `scripts/prompts_and_tool_schemas.py` |
| `scorer_audit.csv` | 40 runs labelled by hand, used to check both scorers. | Hand labels |

The failure codes (A to M) are defined in the "Failure codes" table at the end of `REPORT.md` and in the glossary of `index.html`.

## Scripts

### Evals (in `eval/`, run from the repository root)

| Script | What it does |
|---|---|
| `run_fact_eval.py` | Runs the 35 original questions. A run passes only if every key fact is in the reply, every number came from a tool, and the reply is not empty. |
| `run_scenario_eval.py` | Runs the held-out scenarios. It also checks the database state after each run. |
| `build_scenarios.py` | Builds the held-out scenarios from `store.db`. |
| `run_tool_eval.py` | Asks each tool's question in different wordings. |
| `run_multiturn_eval.py` | Runs two-turn sessions, with or without memory (`--no-memory`). |
| `pass_k.py` | Computes pass^k and pass@k from saved results, with no agent runs. |
| `analyze_failures.py` | Counts the failure modes in saved `run_fact_eval` results. |
| `run_eval.py` | The original, unscored runner from the challenge. |

Each eval run uses a fresh copy of `store.db`, so `initiate_return` never changes the real database. The unit tests in `tests/test_tools.py` (13 tests, no model) check the tools: `python -m unittest discover tests`.

### Traces, labels and schemas (in `scripts/`)

| Script | What it does |
|---|---|
| `collect_traces.py` | Runs one stage's agent on the 35 original questions and 12 edge cases, and saves full traces. |
| `labels.py` | Joins the traces with the hand labels and the database truth, and writes a `*_labels.csv` file. |
| `label_data.py`, `label_data_iteration_1.py`, `label_data_docstrings_only.py`, `label_data_better_tool_docstring.py` | The hand labels for the baseline, iteration 1, iteration 2 and the JSON side experiment. |
| `db_facts.py` | The database query and the facts behind each question. `labels.py` uses it for the `db_truth` column. |
| `trace_store.py` | Loads and indexes trace files. |
| `prompts_and_tool_schemas.py` | Saves the system prompt and tool schemas of each stage's code. It needs no model. |
| `json_variant_tools.py` | The JSON-output version of `src/agent/tools.py`, used only for the side experiment. |

## Reproduce

No model is needed to check the numbers in the report. They come from the files in `results/`:

```bash
PY=$(poetry env info -p)/bin/python
$PY -m eval.pass_k abhi_report/results/iteration_2_heldout_scenarios.json
$PY -m eval.pass_k abhi_report/results/iteration_2_original_questions.json --key pass_asked
$PY -m eval.analyze_failures abhi_report/results/baseline_original_questions.json abhi_report/results/iteration_1_original_questions.json

# Rebuild a label file exactly from its traces
cd abhi_report/scripts
$PY labels.py --labels label_data_docstrings_only ../results/iteration_2_traces.jsonl /tmp/iteration_2_labels.csv ../../store.db
cmp /tmp/iteration_2_labels.csv ../results/iteration_2_labels.csv && echo identical
```

To rerun the agent itself, start Ollama with `qwen2.5:3b` and follow "How to regenerate the results" at the end of `REPORT.md`. A rerun gives new replies, so the numbers will move within the run-to-run noise.

