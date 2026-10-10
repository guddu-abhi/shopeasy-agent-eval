# ShopEasy Support Agent: Evaluation and Improvement Report

This report explains how I defined performance for the ShopEasy support agent, why the baseline fell short, what I changed, and what I would do next. The model stays `qwen2.5:3b` throughout, and the agent is still a LangGraph ReAct agent with tools.

There are two appendices:

- **[`error_analysis.md`](error_analysis.md)** is the full error analysis of the baseline. The data behind it is in [`error_analysis_data/`](error_analysis_data/).
- **[`prompt_tuning.md`](prompt_tuning.md)** is the step-by-step log of every prompt and tool change (V1–V7).

---

## 1. Summary

| Metric (3B model, same harness for both) | Baseline (`main`) | Final (this branch) |
|---|---|---|
| **35 original queries: pass^1** (3 runs each) | 43/105 (41%), CI 32–51% | **89/105 (85%)**, CI 77–90% |
| **35 original queries: pass^3**, all 3 runs pass | 23%, CI 9–37% | **80%**, CI 66–91% |
| 35 queries, asked-for criteria: pass^1 / pass^3 | 46% / 34% | **93% / 91%** |
| **Held-out scenarios: pass^1** (43 new, 2 runs, never tuned on) | 60/86 (70%), CI 59–78% | **74/86 (86%)**, CI 77–92% |
| Held-out scenarios: pass^2 | 63% | **79%** |
| Multi-turn sessions: pass^1 (6 sessions, 3 runs) | 10/18 (56%) | **17/18 (94%)** |
| Empty replies (35 queries) | 3/105 | **0/105** |

- **Definitions.** pass^k is the chance that k runs of the same question *all* pass, as in τ-bench (section 2).
  - The pass^1 intervals are 95% Wilson intervals. The pass^k intervals come from a bootstrap over queries.
  - A run passes only if every check passes: the key facts are in the reply, every number in it came from a tool, and it is not empty.
- **The gain is large, and it holds up across repeated runs.** The baseline answered only 23% of the original questions correctly in all 3 runs; the final version does so for 80%. For a support agent, where each customer gets one try, this is the figure that matters most.
- **On unseen cases, the gain is real but smaller: +16 points, not +44.** The 35 queries were used to choose between versions, so their score is optimistic. The held-out set is the honest estimate.
- **The prompt and the tools fixed different failures.**
  - **The prompt** removed invented query syntax, skipped returns and empty replies.
  - **The tools** removed guessed product IDs, which no prompt wording fixed. This 3B model does not chain tools: it read an ID from one result and passed it on in only 2 of 60 runs. So the tools now accept what customers actually say, a product name.
- **Two release blockers remain, and neither is caught by the original 35 queries:**
  - **A privacy leak.** Asked for "my orders" without an email, the agent searched the prompt's example email in 3 of 12 runs, and showed a real customer's orders.
  - **Invented answers to questions the data can't answer,** such as a "top-rated" shoe when the store has no ratings.
- **One gap in measurement remains.** The automated checks cannot see most false statements (section 4.2). The hand labels found false claims in 41 of 141 baseline traces, but the code's groundedness check flagged 0 of 105 baseline runs.

---

## 2. What performance means at this stage

This is a prototype support agent that reads a store database and can create returns. At this stage, performance should mean **"does it give the customer a correct answer from the data, and does it avoid doing harm?"** It should not yet mean tone, speed or cost.

| Level | Criterion | How it is checked |
|---|---|---|
| **Release blocker** | Never states a fact the tools did not return (an invented ID, price, stock count or ranking) | Groundedness check, code-based; partial (section 4.2) |
| **Release blocker** | Never answers about the wrong entity (another product's stock) | Key-fact check, plus manual review |
| **Release blocker** | Write actions are correct: a return is created only when allowed, never twice | DB state check after each run |
| **Release blocker** | No empty replies; never shows another customer's data | Non-empty check; session-isolation scenario |
| **Core metric** | The reply contains what the customer asked for | Binary pass per query, reported as pass^k |
| **Tolerable for now** | Missing details nobody asked for; wording; shortened product names | Not counted under the asked-for criteria |

- **Why a binary pass per query.** The earlier metric counted facts found (114/156). It gave one query 11 facts and another 1, so two inventory queries dominated the total. It also gave partial credit to wrong answers. A binary pass is easier to read ("30 of 35 questions answered correctly") and easier to label by hand.
- **Why pass^k is the headline.** The agent is not deterministic: in the baseline, 17 of 47 queries got different results across 3 runs of the same input. A customer gets one answer, so what matters is whether the agent is right *every time*.
  - pass^k (from τ-bench) measures that directly. It falls as k grows when an agent is flaky.
  - pass@k (at least one of k runs passes) measures whether the agent *can ever* succeed. It matters little for support, so I report it only to show flakiness: on the baseline, pass@3 is 57% but pass^3 is only 23%.
  - Both are computed by `eval/pass_k.py` from the saved runs, with no new agent calls.

---

## 3. Error analysis of the baseline

I followed the error-analysis process in Hamel Husain and Shreya Shankar's [LLM Evals FAQ](https://hamel.dev/blog/posts/evals-faq/), and ran it before changing anything.

- **Data:** the `main` agent ran on the 35 eval queries plus 12 edge cases I wrote from the DB before any run. That gives 47 queries × 3 runs = **141 traces**, each with every message, tool call and tool result ([`traces.jsonl`](error_analysis_data/traces.jsonl)). Each trace used a fresh copy of `store.db`.
- **Labels:** I read every trace and recorded the first failure, whether the reply states something false, and a note ([`labels.csv`](error_analysis_data/labels.csv)). Each row of the CSV reads as one story: the question, the tool calls, the reply, the DB truth with the SQL to check it, and the verdict.
- **Consistency check:** all 117 recorded tool results match a replay of the same calls on `store.db`, and every final answer was re-read against the DB (`error_analysis.md`, section 8).

**Result: 57 of 141 traces pass (40%).** The 84 failures, by first failure, sorted by share:

| Code | Failure mode | Fails | Share | Of which false claims | Example |
|---|---|---:|---:|---:|---|
| **A** | Invents an ID instead of searching | 22 | 26% | 5 | `check_inventory(123)` → Cooler Bag → "the hammock is not in stock" (70 units) |
| **B** | Asks the user instead of looking it up | 15 | 18% | 0 | "Could you provide the product ID?" |
| **D** | Invents query syntax | 10 | 12% | **9** | `search_orders("email:bianca@…")` → "no orders found" (she has 3) |
| **F** | Return action not executed | 7 | 8% | 5 | Looks up the order, then asks "shall I proceed?" |
| **C** | Empty response | 7 | 8% | 0 | `""` |
| **L** | Calls the order date a delivery date | 6 | 7% | **6** | "delivered on 2026-01-18" (the order date) |
| **H** | Invents policy or facts | 5 | 6% | **5** | "30-day return policy"; no policy data exists |
| **E** | Search term misses catalog words, no retry | 4 | 5% | 4 | "skincare" → nothing (the category is Beauty) |
| **J** | Misreads tool output | 4 | 5% | 4 | Swaps two orders' statuses |
| **K** | Tool rejects valid input | 3 | 4% | 3 | `Alice@Example.com` → no orders (exact, case-sensitive match) |
| **I** | Stops mid-chain | 1 | 1% | 0 | Finds product #46, then asks the user to run `check_inventory` |

**What this shows:**

- **Most failures happen before the model sees any data.** In 61 of 84 failures (73%), the model made no tool call (B, C), sent wrong arguments (A, D), or the search found nothing (E, K). The fix is in tool design and tool-calling, not in answer wording.
- **Frequency and harm rank differently.**
  - About half the failures (41 of 84) tell the customer something false, and the customer has no reason to doubt it.
  - D and L are mid-ranked by frequency, but almost every one is a false statement. A is the most frequent mode, but mostly produces "I couldn't find ID 12345", which is unhelpful but true.
- **How the user names the entity predicts failure better than the question category does.**

  | How the user names it | Pass rate |
  |---|---|
  | Product name | 4/27 (15%) |
  | Category | 4/18 (22%) |
  | Email | 7/24 (29%) |
  | Order ID | 38/63 (60%) |

  The baseline agent works only when it is handed an ID.
- **These counts describe the test set, not real traffic.** The queries are curated and partly synthetic.

**Problems found in the eval set itself:**
- **Unreachable facts.** Q18 and Q31 expect the refund of an existing return, and Q18, Q23 and Q31 expect its reason. The original `initiate_return` returned neither, so no agent could pass. Q5 expects stock counts that `search_products` never returns.
- **Incomplete or inconsistent references.**
  - Q16's reference lists one pair of sunglasses, but the store sells two (#16 and #78).
  - Q18 says the boots came in the "wrong color", but the existing return says "sole separated after one hike".
  - Q13 is labelled `order_status`, but it asks for order details.
- **The eval wrote to the real database.** `initiate_return` writes to `store.db` (it did so in 1 of 3 baseline runs of Q4), so later runs of Q4 see a different DB. Every harness here now uses a fresh copy of the DB.
- **Seed dates.** `returns.created_at` is set when the seed script runs, so every return looks as if it was filed months after delivery.

---

## 4. From failures to evals

### 4.1 One check per failure mode

| Failure mode | Check | Type | Where | Validated by |
|---|---|---|---|---|
| A: invented ID | Every `*_id` argument must appear in the user message or an earlier tool result | Code | `labels.py` (ID-grounding check) | Flags exactly the 22 A traces among 81 ID calls, with 0 false flags |
| B, I: no lookup, no chaining | Key facts in the reply | Code | `eval/run_fact_eval.py` | Scorer audit (4.3) |
| C: empty reply | Reply is not empty | Code | All evals | Trivially exact |
| D, E, K: retrieval misses | Key facts (order IDs, product names) in the reply; email, partial-name and not-found cases | Code | `run_fact_eval.py`, `run_scenario_eval.py` | Expected values come from SQL |
| F: return not executed | DB state after the run | Code | `run_scenario_eval.py` | — |
| Generalisation | 43 held-out scenarios built from 4 dimensions; 16 intents × 4–5 paraphrases; 6 multi-turn sessions | Code | `build_scenarios.py`, `run_tool_eval.py`, `run_multiturn_eval.py` | Never used for tuning |
| H, J, L: false statements | **No reliable automated check yet** | — | — | See 4.2 |

**Two taxonomies, one mapping.** `eval/analyze_failures.py` applies a code-detectable version of these modes to any results file, so before and after can be compared automatically. A = `guessed_id`, B = `no_tool_call`, C = `empty_reply`, D = `invented_syntax`, E, I and K = `data_not_retrieved`, and F = `skipped_write_action`. H, J and L have no code equivalent.

| Failed runs (35 queries, 3 runs, asked-for criteria) | Baseline | V7 | Final |
|---|---:|---:|---:|
| `guessed_id` | 15 | 0 | 0 |
| `no_tool_call` | 14 | 0 | 0 |
| `invented_syntax` | 11 | 0 | 0 |
| `data_not_retrieved` | 7 | 13 | 6 |
| `skipped_write_action` | 6 | 0 | 0 |
| `empty_reply` | 3 | 0 | 0 |
| `dropped_fact` | 1 | 1 | 1 |
| **Total** | **57/105** | **14/105** | **7/105** |

### 4.2 The gap: false statements

- **The groundedness check flagged 0 of 105 baseline runs.** It checks that every *number* in a reply came from a tool. The baseline's false claims are mostly not numbers: "no orders found", "not in stock", an invented "30-day return policy", or an order date presented as a delivery date.
- **So this harm is currently measured only by hand.** The hand labels mark 41 of 141 baseline traces as false claims. That rate is not measured for the final version, and section 7 treats this as a limitation.
- **The plan to close it:**
  - **A code check for L:** flag "shipped/delivered on <date>" when that date is the order's `created_at`.
  - **An LLM judge for H and J,** for "states a fact not in the tool output". The 141 hand-labelled traces are a ready-made validation set: the `false_claim` column is the gold label. Report the judge's TPR and TNR on them before trusting it on new runs.
  - **The judge may use a different, larger model.** The constraint is on the agent's model, not the grader's.

### 4.3 Checking the scorer

A code grader can be wrong too, so I checked it against hand labels. I sampled 40 runs (20 baseline, 20 final, mixing scorer passes and fails) and labelled each reply as a support lead would (`report/results/label_audit.csv`).

| Scorer | Failures caught (TPR) | Good replies passed (TNR) | Agreement |
|---|---|---|---|
| Strict key facts (from `expected_answer`) | 13/17 (76%) | 16/23 (70%) | 72% |
| **Asked-for key facts** | 12/17 (71%) | **21/23 (91%)** | **82%** |

- **The strict scorer fails correct answers.** The expected answers include details nobody asked for, such as a tracking number for "what carrier… and when will it arrive?". The asked-for view checks only what the question asks, for 11 queries, with the reason recorded next to each one. Both views are reported.
- **Both scorers miss mislabelled dates** (4 of their 5 missed failures). This matches the gap in 4.2.
- **Two independent baseline samples agree.** The hand-labelled traces (41/105 on the 35 queries) and the code-graded baseline runs (43/105) are different runs scored by different graders. Their pass rates differ by 2 points.

---

## 5. What changed and why

Each change followed the same loop: a hypothesis from a failure mode, one change, then a measurement on the evals. The change was kept only if it helped. The full log is in `prompt_tuning.md`.

| Change | Failure mode it targets | Evidence |
|---|---|---|
| **Prompt:** one example per tool showing a question and its exact tool call, the exact tool names, and "never guess an ID" (V2) | B, C, D | Facts found: 76 → 89 of 156. Empty replies were traced to tool names the model invented. |
| **New `list_categories` tool,** with keyword matching and fallbacks (V4–V6) | E, plus "what do you sell?" questions | Book questions: 0/12 → 12/12 |
| **`get_product_details` and `check_inventory` accept a name,** not just an ID (V7) | A, I | Prompting the model to chain calls worked in 2 of 60 runs; name-accepting tools passed 48/48 |
| **`initiate_return` reports an existing return's reason and refund** | F, and the unreachable facts | Returns: 6/12 → 12/12 |
| **Product names match whole words;** near-misses are flagged as "No exact match" | Wrong-entity answers introduced by V7 | "Nike Air Max" had matched "Hair Clip Set". Unit tests cover this. |
| **Session memory,** opt-in per thread | Follow-up turns lost context | Section 6.3 |

**What did not work, and what it taught me:**

- **A concise rewrite of the prompt (Step 6) caused empty replies.** The examples were written in plain text and showed only one tool. The model then invented tool names (`get_order_status`), and Ollama dropped those calls. I found this by sampling the raw model output, and fixed it by stating the exact tool names.
- **Spelling out multi-step sequences in the prompt (V3) did not help.** The score did not improve (85–86 vs 89 facts), and empty replies rose to 5–6 of 70. I reverted it. Under every prompt I tried, the model made one tool call and answered from it.
- **Lesson: fit the tools to the model.** A 3B model will not reliably chain dependent calls. Rather than keep rewording the prompt, I made each answer need only one call.
- **New risk created by the tool fix.** Fuzzy name matching moved the wrong-entity risk into the tool: for a product the store doesn't sell, the tool returned a similar one. The tool now says "No exact match for 'X'. Closest products (not the same item…)".

---

## 6. Results

### 6.1 Reliability across runs (pass^k)

| Eval | Version | pass^1 | pass^2 | pass^3 | pass@3 |
|---|---|---:|---:|---:|---:|
| 35 queries, strict | Baseline | 41% | 30% | 23% | 57% |
| | Final | **85%** | **82%** | **80%** | 89% |
| 35 queries, asked-for | Baseline | 46% | 38% | 34% | 57% |
| | Final | **93%** | **92%** | **91%** | 94% |
| Held-out scenarios (2 runs) | Baseline | 70% | 63% | — | — |
| | Final | **86%** | **79%** | — | — |
| Multi-turn sessions | No memory | 56% | 50% | 50% | 67% |
| | Memory | **94%** | 89% | 83% | 100% |

- **The final version is both better and steadier.** Its pass^k drops by only 5 points from k=1 to k=3, compared with 18 for the baseline.
- **The held-out set drops more** (86% → 79% from k=1 to k=2). Some held-out questions are answered correctly only some of the time, so this is where reliability work should go next.

### 6.2 Held-out scenarios by dimension

The held-out scenarios are built from four dimensions (`eval/build_scenarios.py`):
- the intent;
- how the entity is named (ID, exact or partial name, email, none, or one that doesn't exist);
- the data state (normal, pending, return exists, not sold, not found);
- the phrasing (formal or casual).

Expected values come from SQL, and no entity overlaps with the tuning sets or the prompt's examples. Two checks in my generator were too strict, so both systems were re-scored from their saved runs after the fix. Before that fix, the baseline scored 62/86 and the final version 68/86.

| Dimension | Baseline | Final |
|---|---|---|
| **All** | 60/86 (70%) | **74/86 (86%)** |
| Named by ID | 39/46 | 42/46 |
| Named by exact / partial name | 2/8 / 1/6 | **5/8 / 6/6** |
| Named by email | 2/6 | **6/6** |
| Entity does not exist | 14/14 | 13/14 |
| inventory | 11/22 | **18/22** |
| order_lookup | 4/10 | **10/10** |
| returns | 9/14 | 11/14 |
| shipping | 12/12 | 11/12 |
| out_of_scope ("best reviewed…") | 2/4 | **0/4** |

The final version wins where the baseline had to turn a name or an email into a tool call, which matches the error analysis. It is no better on ID-based questions, which already worked. It is worse on questions it should decline.

### 6.3 Robustness: personas and conversations

The 35 queries are all single, well-formed questions. I tested two kinds of customer behaviour they don't cover.

**Phrasing persona: formal vs casual** (held-out scenarios, e.g. "Could you tell me whether the X is in stock?" vs "hey do u have any X left? how many").

| Phrasing | Baseline pass^1 | Final pass^1 | Final pass^2 |
|---|---|---|---|
| Formal (24 scenarios) | 34/48 (71%) | **42/48 (88%)** | 79% |
| Casual (19 scenarios) | 26/38 (68%) | **32/38 (84%)** | 79% |

- **Both personas improve by about 16 points, and the gap between them stays small.** The remaining casual failures come from tool choice, not tone. For example, "how many left?" goes to `list_categories`, which has no stock counts. So more tone-based personas would add little until tool selection is fixed.

**Conversation persona: the customer who answers over several turns** (6 sessions × 3 runs).

| Session | No memory | Memory |
|---|---|---|
| Missing email, then given | 3/3 | 3/3 |
| Return without an order number, then given | 1/3 | **3/3** |
| Product follow-up with a pronoun ("how much does it cost?") | 0/3 | **3/3** |
| Order follow-up ("who is shipping it?") | 0/3 | **3/3** |
| Customer corrects the product | 3/3 | 3/3 |
| No leak between two customers' sessions | 3/3 | 2/3 |
| **All** | 10/18 (56%) | **17/18 (94%)** |

- **The sessions that need context go from 1 of 9 runs to 9 of 9.** `Agent.run` used to start a new conversation on every call. It now takes a LangGraph `MemorySaver`, opt-in per `thread_id`.
- **Memory does not fix tool chaining.** Chaining fails within a single turn.
- **The one failure with memory is not a leak between sessions.** It is the privacy blocker in 6.4.

### 6.4 Regressions and release blockers

- **Prompt examples are used as defaults, which leaks private data.** When a customer asked for "my orders" without an email (12 runs), the agent:
  - asked for the email first in 0 runs;
  - searched an invented placeholder email in 9 runs;
  - searched **`grace@example.com`**, the prompt's example, and listed Grace Kim's orders, in **3 runs**.

  Without memory, follow-ups about "it" were also answered with the prompt's example order IDs (#22, #44). The fact scorer cannot catch this, because the reply looks fine; catching it needs a check on the tool **arguments**.
- **Invented rankings: 0/4 on questions the data can't answer.** "whats ur top rated running shoe" → "One of the top-rated running shoes is the Blue Ultraboost…". The baseline declined correctly in 2 of 4 runs, so this is a regression. A likely cause is the prompt's "get facts only by calling a tool" rule, which says nothing about what to do when no tool can answer.

---

## 7. Limitations

- **One labeller.** I labelled every trace and the scorer audit myself. A domain expert should review `labels.csv`, especially the 11 `borderline` passes, before anyone builds evaluators on these labels.
- **Small samples.** There are 35 + 43 queries with 2–3 runs each, so the intervals are wide: pass^3 on the 35 queries spans 66–91%. Differences inside an interval are treated as noise.
- **Selection bias.** I chose between versions using the 35 queries and the paraphrase set, so their scores are optimistic. Only the held-out set and the multi-turn sessions were never used for tuning.
- **Unmeasured harm.** The false-claim rate of the final version is not measured (section 4.2). Its 0 ungrounded *numbers* does not mean it makes no false statements.
- **No ablation.** The prompt and tool changes were not tested separately on the final total, so I don't rank their contributions.

---

## 8. Next steps, in priority order

1. **Never show one customer another customer's data (6.4).**
   - Replace the prompt's example entities with ones that do not exist in the store.
   - Add a deterministic guardrail in the graph: before `search_orders` runs, check that the email appears in the customer's messages, and otherwise ask for it.
   - Add the same argument check to the evals, with "my orders" and "my last order" cases that give no entity.
   - This comes first because it is the only failure that harms a third party, and the prompt rule alone does not prevent it.
2. **Measure false statements automatically (4.2).**
   - Add the order-date check for L.
   - Build one LLM judge for "states a fact not in the tool output", and validate it on the 141 hand-labelled traces (TPR and TNR on the `false_claim` column) before using it.
   - Until this exists, the most harmful failure mode is visible only by hand.
3. **Stop invented answers on questions the data cannot answer.**
   - Add a prompt rule: "we have no ratings, reviews or policies; say so".
   - Add 10–15 held-out cases (ratings, delivery promises, discounts), and gate releases on them.
4. **Label dates in the tool outputs.** `search_orders` and `lookup_order` print bare dates, which the agent reads as delivery dates. Print "ordered 2026-04-10", and show `shipped_at` and the delivery date only where they exist.
5. **Fix catalog retrieval for stock and category questions.** This causes the remaining failures: "fitness equipment" → Electronics, "skincare" with no synonym, and casual "how many left" questions sent to `list_categories`.
   - Either include stock counts in `list_categories`, or split it into `list_categories()` and `list_products(category)`.
   - Measure each option on the tool eval and the held-out set separately.

**Deliberately not prioritized:**
- **Multi-agent routing.** Order intents already pass 10/10 on the held-out set. A router would add a new failure point without a failure that needs it.
- **More tone-based personas.** Casual and formal phrasing improved equally (6.3), and the casual failures come from tool choice. More personas are worth adding only if trace review shows that tone changes the outcome.

---

## Appendix: reproducing the results

```bash
# Unit tests for the tools
poetry run python -m unittest discover tests

# Evals (each run uses a fresh copy of store.db)
poetry run python -m eval.run_fact_eval --runs 3 --out report/results/fact_eval_v8.json
poetry run python -m eval.run_scenario_eval --runs 2 --out report/results/scenarios_v8.json
poetry run python -m eval.run_multiturn_eval --runs 3 --out report/results/multiturn_memory.json
poetry run python -m eval.run_multiturn_eval --runs 3 --no-memory --out report/results/multiturn_no_memory.json

# Analysis of saved runs (no agent calls)
poetry run python -m eval.analyze_failures report/results/fact_eval_baseline.json report/results/fact_eval_v8.json
python3 -m eval.pass_k report/results/fact_eval_baseline.json report/results/fact_eval_v8.json
python3 -m eval.pass_k --key pass_asked report/results/fact_eval_baseline.json report/results/fact_eval_v8.json
python3 -m eval.pass_k --by phrasing report/results/scenarios_baseline.json report/results/scenarios_v8.json
python3 -m eval.pass_k report/results/multiturn_no_memory.json report/results/multiturn_memory.json

# Baseline error analysis: counts, ID-grounding check and labels.csv
python3 report/error_analysis_data/labels.py report/error_analysis_data/traces.jsonl report/error_analysis_data/labels.csv
```

The baseline evals were run by extracting the `main` branch (`git archive 029ffaf src`) into a separate folder, adding the same `eval/` files, and running the same commands there. The baseline traces for the error analysis were collected with `report/error_analysis_data/collect_traces.py` on `main`.
