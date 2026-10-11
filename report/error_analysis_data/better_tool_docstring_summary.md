# Better tool docstrings: re-run of every eval, and labels for 141 new traces

This version changes `src/agent/tools.py` in two ways at once. **The docstrings and argument descriptions** now say when to use each tool and what it returns. **The tool outputs** are now JSON from small Pydantic models, with fields such as `order_date`, `quantity_available`, `note` and `error`. Both changes shipped together, so **no result below can separate the effect of the docstrings from the effect of the outputs.**

- **Setup:** the commit is `ee1be43f13ee9a5c9088239c802bb06d9d19be9a`, with uncommitted changes to `src/agent/tools.py`, `eval/run_fact_eval.py` (`LINE_ITEM` only) and `tests/test_tools.py`. Those three files are saved in `report/iterations/better_tool_docstring_src/`. The model is `qwen2.5:3b` on Ollama, and the 13 unit tests pass. Every run used a fresh copy of `store.db`. All runs took place on 2026-10-10, 19:24–19:40.
- **Comparison columns:** the comparisons use three versions.
  - **Baseline** is `main`.
  - **v8** is the final version in REPORT.md. Its tool-eval file is the committed copy, because the working-tree copy of `report/results/tool_eval_v8.json` has a stray edit that makes it invalid JSON. That file was left untouched.
  - **New** is this version.
- **Hand labels:** these exist only for the baseline and for this version. v8 has no labelled traces, so the label comparisons below are **baseline → new**. They measure every change since `main`, not the docstring change alone.

## 1. Headline table

The table repeats the REPORT.md section 1 table, with a column for this version. Each pass^1 interval is a 95% Wilson interval, and each pass^k interval is a bootstrap over queries, both as in the report.

| Metric (3B model, same harness) | Baseline (`main`) | v8 (REPORT.md final) | **New (better docstrings + JSON outputs)** |
|---|---|---|---|
| **35 original queries: pass^1** (3 runs each) | 43/105 (41%), CI 32–51% | 89/105 (85%), CI 77–90% | **81/105 (77%)**, CI 68–84% |
| **35 original queries: pass^3**, all 3 runs pass | 23%, CI 9–37% | 80%, CI 66–91% | **71%**, CI 57–86% |
| 35 queries, asked-for criteria: pass^1 / pass^3 | 46% / 34% | 93% / 91% | **84%** (CI 76–90%) / **77%** (CI 63–89%) |
| **Held-out scenarios: pass^1** (43 scenarios, 2 runs) | 60/86 (70%), CI 59–78% | 74/86 (86%), CI 77–92% | **77/86 (90%)**, CI 81–94% |
| Held-out scenarios: pass^2 | 63% | 79% | **86%**, CI 74–95% |
| Multi-turn sessions: pass^1 (6 sessions, 3 runs) | 10/18 (56%) | 17/18 (94%) | **17/18 (94%)**, CI 74–99% |
| Empty replies (35 queries) | 3/105 | 0/105 | **0/105** |
| Tool-call eval (64 runs, `--runs 4 --seed 0`) | — | 61/64 (95%), CI 87–98% | **56/64 (88%)**, CI 77–94% |
| Hand labels: traces that pass (141) | 57/141 (40%), CI 33–49% | not labelled | **98/141 (70%)**, CI 61–77% |
| Hand labels: traces with a false claim (141) | 41/141 (29%), CI 22–37% | not labelled | **33/141 (23%)**, CI 17–31% |

**Notes on the table**

- **No difference from v8 is outside the noise.** Every new-vs-v8 interval overlaps the v8 interval. The fact eval fell by 8–9 points and the tool eval by 5 runs, but both stay inside the intervals. The rise on the held-out scenarios is also inside them.
- **Multi-turn without memory** fell from 10/18 to 8/18 (CI 25–66%). The interval is wide, so this is noise too. With memory, the result is 17/18 in both versions.
- **Tool eval settings:** `--runs 4 --seed 0` reproduces the exact questions in `tool_eval_v8.json`. I checked this by replaying the paraphrase picker, with no agent calls. Seeds 1–9 do not match.

## 2. Failure modes (hand labels, 141 traces each)

The traces are the same 47 queries × 3 runs as the baseline. I used the same codebook (`report/error_analysis.md`), plus one new code, M. These are first-failure counts.

| Code | Failure mode | Baseline | New | Of which false claims (new) |
|---|---|---:|---:|---:|
| A | Invents an ID instead of searching | 22 | 5 | 3 |
| B | Asks the user instead of looking it up | 15 | **0** | — |
| D | Invents query syntax | 10 | **0** | — |
| F | Return action not executed | 7 | **0** | — |
| C | Empty response | 7 | **0** | — |
| L | Calls the order date a ship or delivery date | 6 | **11** | 11 |
| H | Invents policy or facts | 5 | 1 | 1 |
| E | Search term misses catalog words, no retry | 4 | 6 | 2 |
| J | Misreads tool output (other than dates) | 4 | **12** | 12 |
| K | Tool rejects valid input (case-sensitive email) | 3 | 3 | 3 |
| I | Stops mid-chain | 1 | 3 | 0 |
| **M** (new) | **Garbled word in the reply** | — | 2 | 1 |
| **Fails** | | **84** | **43** | **33** |

**New code M: garbled word in the reply.** The reply contains a non-word where a field value should be, for example "shased" or "Shashted" for `"shipped"`. This happens in 20 run 0, 20 run 2 (recorded under J, which comes first) and S7 run 1. The fact eval shows it again in Q9 runs 0 and 1. It never occurs in the 141 baseline traces. J does not fit, because the model has not misread the meaning; it has corrupted the word.

**False claims, measured for the first time beyond the baseline (REPORT.md section 4.2)**

- **Share of all traces:** 41/141 (29%) for the baseline, and **33/141 (23%)** now. The intervals overlap (22–37% and 17–31%), so the rate has not clearly fallen.
- **Share of failures:** 41/84 (49%) for the baseline, and **33/43 (77%)** now. The agent fails half as often. However, when it fails, it now usually tells the customer something false rather than something unhelpful.
- **Where the failures happen:** 26 of 43 failures (60%) now happen at the *answer faithfully* step (J, L, H, M), compared with 15 of 84 in the baseline. Only 14 failures stop the data from reaching the model (A, E, K), compared with 61 in the baseline.
- **The code checks still miss these.** The fact eval's groundedness check flagged 0 of 105 new runs, the same as before.

**Code L persists, and it is more frequent than in the baseline.**

- **Count:** 17 traces call an order date a ship, delivery or cancel date: 11 as the first failure and 6 as a secondary code. The baseline had 11. This happens even though the field is now named `order_date`.
  - **First failure:** 7 runs 0–1, 14 runs 0–1, 15 run 0, 25 runs 0–2, 33 runs 0 and 2, and 34 run 0.
  - **Secondary:** 20 runs 0 and 2, 30 run 0, 34 run 2, S6 run 1 and S11 run 2.
- **Check:** an automated scan of every reply, for an `order_date` value next to "delivered", "shipped", "cancelled" or "arrived", found no case beyond these 17.
- **Pattern:** L occurs mainly for delivered orders ("Order #40 was delivered on 2026-01-18") and in order lists ("Order #46, delivered on February 15, 2026").
- **The fact eval shows it too.** Q15 runs 0 and 1 say "delivered on 2026-01-30", which is the order date. The fact scorer cannot detect this.

## 3. ID-grounding check

The check is in `labels.py`. It passes when every `*_id` argument appears in the user message or in an earlier tool result.

- **Result:** of 69 ID-argument calls, the check flags 5 traces. All 5 are the code-A traces (S6 runs 0–2 and S9 runs 0–1), and there are 0 false flags. The baseline result was 22 of 22, with 0 false flags.
- **Which invented IDs:** the IDs here are 50, 14, 12345, 1 and 0. The `misc` counter in `labels.py` looks only for 123, 12345 and 123456, so it reports just 1 of the 5. The grounding check catches all of them.
- **Limitation:** product tools now take `product` (a name or an ID), not `product_id`, so the check no longer covers product lookups. In these traces, the only numeric product reference is `"4"` in Q17, and it comes from the user's message.

## 4. Changes

"Noise" means the difference is inside the confidence intervals.

### Against v8 (code evals): no significant change

The per-query shifts below are consistent across runs, so they are worth checking. They do not prove a regression.

- **The `initiate_return` replies drop the refund amount.**
  - **Evidence:** in the tool eval, `initiate_return` fell from 8/8 to 5/8 (IDs 15 and 16). In the fact eval, Q4 run 1 fails this way. In the scenario eval, scenario 35 runs 0–1 do too.
  - **Pattern:** the replies repeat the new `note` ("The refund is pending approval") instead of the `refund_amount` field.
- **The agent routes to `search_products` with a multi-word query.**
  - **Evidence:** fact Q22 fell from 3/3 to 1/3. v8 called `list_categories("books")`. The new agent calls `search_products("book cooking")`, gets no match, and says there are no cooking books.
  - **Docstring:** the `search_products` docstring now says to use it "when the customer asks whether the store sells something". The argument description ("one short keyword") is ignored.
  - **Traces:** 22 runs 0–2 fail the same way (E).
- **Q15 replies drop the unit prices.** Fact Q15 fell from 3/3 to 0/3 under the asked-for criteria. The fact eval's asked-for list includes the line prices for this query; the hand rubric does not, so traces 15 runs 1–2 pass.
- **The agent misreads statuses.**
  - **Q12:** fact Q12 fell from 3/3 to 1/3. The agent says "in transit" or "on its way" when the tool returns `out_for_delivery`.
  - **Q9:** fact Q9 fell from 3/3 to 1/3, with "shased".
  - **Analyzer artifact:** `eval.analyze_failures` codes the Q12 runs as `data_not_retrieved`. "Out for delivery" does not literally match the raw value `out_for_delivery`, so it treats the fact as missing from the tool output. The pass/fail result is unaffected.
- **Scenario 42 is a false pass by the scorer, not an improvement.** It went from 0/2 to 2/2, but both new replies invent a ranking: "with good reviews" and "one of the best-reviewed headphones". This is the release blocker in REPORT.md section 1. The scenario scorer does not catch it.

### Against the baseline (hand labels): a clear improvement, but not attributable to the docstrings

The pass rate rose from 40% (CI 33–49%) to 70% (CI 61–77%). This difference is outside the noise. It reflects all the changes since `main`.

**Improvements**

- **The no-tool-call failures are gone.** No trace has B, C, D or F.
- **Product names now work.** Product-name questions pass 24 of 27 traces (89%), up from 4/27. Inventory (18/18), shipping (15/15) and product info (12/12) all pass.
- **Returns now work.** All runs of S2 and S3 pass (the baseline had B and F). Q23 and Q31 report the existing return in every run.
- **The invented return policy is gone from S9.** No run invents a "30-day policy" any more. However, two runs now invent an order ID (see below).

**Regressions**

- **S6, "Where is my order?", fell from 3/3 to 0/3 (A).** This is a privacy leak.
  - The agent calls `lookup_order` with IDs it invented: 50, 14 and 12345.
  - In S6 runs 0 and 1, it presents another customer's order as "your order". Both runs give that customer's name, and run 0 also gives their email.
- **S9, "What is your return policy?", now invents an order ID (A).**
  - Run 0 calls `lookup_order(1)` and describes Alice's order.
  - Run 1 calls the write tool `initiate_return(order_id=0, reason="I don't want it anymore")` with an invented ID and reason. The call failed only because order 0 does not exist.
- **The agent misreads lists of orders (J).** In 7 of the 12 J failures, the agent assigns dates, totals or statuses to the wrong order: 7 run 2, 20 run 2, 30 runs 0–2, 34 run 2 and S11 run 2. In the baseline, email questions usually failed before any data arrived (D).
- **Q9 now says that a shipped order is pending (J).** Runs 1–2 say it "is still pending shipment" and "still pending". Run 0 says it is "being processed". In the baseline, Q9 failed with empty replies (C).
- **S8 still fails all 3 runs, now with I instead of A.** The agent calls `check_inventory` and never gets the price the user asked for.
- **S12 still fails all 3 runs (K).** Email matching is case-sensitive in both v8 and this version, so this was never fixed.

## 5. Pending review

There are 16 labels marked `BORDERLINE:`. `labels.py` counts BORDERLINE only on passes (12). On the 4 fails, the prefix is kept in `label_data_better_tool_docstring.py`. The CSV `note` column drops it, so those 4 are listed here.

| Trace | Label | Why it is a close call |
|---|---|---|
| 4 run 0 | pass | The return was created. The reply omits the refund amount and adds "you should receive a notification … shortly". |
| 4 run 1 | pass | The reply says the refund "is pending approval", then "you will receive a refund of $79.99" as if it were certain. |
| 5 runs 0–2 | pass | The reply lists all 15 in-stock Fitness products with prices, but gives no unit counts, which the reference has. |
| 9 run 0 | **fail (J)** | The reply says the order is "being processed", then "still shipped". It gives no carrier or tracking number. |
| 18 run 2 | **fail (J)** | The reply says the wrong-color issue was "already addressed". The existing return is for a separated sole. |
| 24 run 2 | **fail (H)** | The reply adds product descriptions no tool returned, for example a bottle that "expands to a cup size". |
| 27 run 0 | **fail (E)** | "No skincare products matching that name" is not counted as a false claim, because it reads as the search result. |
| S5 runs 0–2 | pass | The reply offers the Laptop Sleeve but never says that no laptops are sold. |
| S7 run 2 | pass | The reply gives the status and total only, and misses `out_for_delivery`. |
| S10 runs 0–2 | pass | The reply does not confirm that the order is pending. Runs 1–2 also promise "I'll check back later". |

**Other judgement calls a reviewer may want to see**

- **Privacy:** 13 runs 0–2 volunteer the customer's name and email, and are passed, as in the baseline.
- **False claims in E traces:** only E replies that state the store lacks the item count as false claims (22 run 0 and 27 run 1). Replies that say "I couldn't find" do not.

## Files

- `report/results/fact_eval_better_tool_docstring.json`, `scenarios_better_tool_docstring.json`, `multiturn_memory_better_tool_docstring.json`, `multiturn_no_memory_better_tool_docstring.json` and `tool_eval_better_tool_docstring.json`
- `report/error_analysis_data/traces_better_tool_docstring.jsonl`: 141 traces with no errors. Collected with `poetry run python report/error_analysis_data/collect_traces.py . report/error_analysis_data/traces_better_tool_docstring.jsonl 3`.
- `report/error_analysis_data/label_data_better_tool_docstring.py`: the hand labels.
- `report/error_analysis_data/labels_better_tool_docstring.csv`: built with `python3 report/error_analysis_data/labels.py --labels label_data_better_tool_docstring report/error_analysis_data/traces_better_tool_docstring.jsonl report/error_analysis_data/labels_better_tool_docstring.csv`.
- `report/error_analysis_data/labels.py`: now has an optional `--labels MODULE` flag. The default command still rebuilds `labels.csv` byte-for-byte, and the printed counts are unchanged.
