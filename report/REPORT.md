# ShopEasy Support Agent: Evaluation and Improvement Report

This report covers how I defined performance for the ShopEasy agent, how I measured it, what I changed, and what I would do next. The model stays `qwen2.5:3b` throughout, and the agent is still a LangGraph ReAct agent with tools.

The step-by-step history of the prompt and tool changes (V1–V7) is in [`prompt_tuning.md`](prompt_tuning.md). This report is the summary, and that file is the appendix.

---

## 1. Summary

| | Baseline (main branch) | Final (this branch) |
|---|---|---|
| **35 queries, strict pass rate** (3 runs) | 43/105 (41%), CI 32–51% | **89/105 (85%)**, CI 77–90% |
| **35 queries, asked-for pass rate** (section 6) | 48/105 (46%), CI 37–55% | **98/105 (93%)**, CI 87–97% |
| **Held-out scenarios** (43 new, 2 runs, never tuned on) | 60/86 (70%), CI 59–78% | **74/86 (86%)**, CI 77–92% |
| **Multi-turn sessions** (6 sessions, 3 runs) | 10/18 (56%), no memory | **17/18 (94%)**, with memory |
| Empty replies (35 queries) | 3/105 | 0/105 |

CI = 95% Wilson interval. A run passes only if **every** check passes: the key facts are in the reply, every number in the reply came from a tool, and the reply is not empty.

- **The gain is large and consistent on the 35 queries.** The baseline passed 11, 14 and 18 of 35 queries in its three runs. The final version passed 30, 30 and 29. The confidence intervals do not overlap.
- **On unseen cases, the gain is real but smaller: +16 points, not +44.** The 35 queries were used to choose between versions, so their score is optimistic. On the held-out set, ID-based questions barely move (39/46 → 42/46). The gain is in questions that name a product or give an email, which is where the baseline failed (section 5.2).
- **The prompt and the tools fixed different failures** (section 4).
  - **The prompt** removed made-up query syntax, skipped returns and empty replies.
  - **The tools** removed guessed product IDs, which no prompt wording fixed. This 3B model will not chain tools: it almost never reads an ID from one result and passes it to the next tool (2 of 60 runs, `prompt_tuning.md` section 5). So the tools now take what customers actually say, a product name, and return everything the answer needs in one call.
  - No ablation separates the two effects on the total, so I don't rank them.
- **The new evals found two release blockers the 35 queries never test** (sections 5.2 and 5.4):
  - When a customer asks for "my orders" without an email, the agent invents one. In 3 of 12 runs it used `grace@example.com`, the example in the prompt, and **showed a real customer's orders to someone else**.
  - On questions the data cannot answer ("top-rated running shoe"), the final version invents a ranking (0/4 pass). The baseline declined correctly in 2 of 4 runs, so this is a regression.

---

## 2. What performance means at this stage

This is a prototype support agent that reads a store database and can create returns. At this stage, performance should mean **"does it give the customer a correct answer from the data, and does it avoid doing harm?"** It should not yet mean tone, speed or cost.

| Level | Criterion | How it is checked |
|---|---|---|
| **Release blocker** | Never states a fact the tools did not return (an invented ID, price, stock count or ranking) | Groundedness check, code-based |
| **Release blocker** | Never answers about the wrong entity (another product's stock) | Key-fact check, plus manual review |
| **Release blocker** | Write actions are correct: a return is created only when allowed, never twice | DB state check after each run |
| **Release blocker** | No empty replies; never shows another customer's data | Non-empty check; session-isolation scenario; tool-argument check (to add, section 5.4) |
| **Core metric** | The reply contains what the customer asked for | Binary pass per query, by intent |
| **Tolerable for now** | Missing details nobody asked for; wording; shortened product names | Not counted under asked-for criteria |

**Why a binary pass per query instead of "facts found":** the earlier metric (114/156 facts) gave one query 11 facts and another one fact, so two inventory queries dominated the total. It also gave partial credit to wrong answers. A binary pass per query is easier to read ("30 of 35 questions answered correctly") and easier to label by hand.

---

## 3. How it is measured

| Eval | What it answers | Size | Grader |
|---|---|---|---|
| `eval/run_fact_eval.py` | Does the agent answer the 35 original queries? | 35 queries × 3 runs | Code: key facts, groundedness, non-empty |
| `eval/run_tool_eval.py` | Does it give the same answer to the same question in other words? | 16 intents × 4–5 paraphrases | Code: key facts; tool called |
| `eval/run_scenario_eval.py` | Does it work on cases it was never tuned on? | 43 scenarios × 2 runs | Code: facts, declines, groundedness, DB state |
| `eval/run_multiturn_eval.py` | Does it keep context across turns, and only within a session? | 6 sessions × 3 runs | Code: facts in the final reply, no leaks, DB state |
| `tests/test_tools.py` | Do the tools return the right data? | 13 tests | Unit tests, no LLM |
| `.github/workflows/eval.yml` | Did a change break something? | Unit tests on every push; 8-query LLM smoke test on PRs | Pass rate ≥ 60%: the final version scores 79% and the baseline 54% on these 8 queries, so the threshold catches a fall back to baseline quality without failing on noise |

**Method notes:**
- Every run uses a fresh copy of `store.db`, because `initiate_return` writes rows. `store.db` has the same checksum before and after all runs.
- The agent is stochastic, so every number is a pass rate over repeated runs with a confidence interval. Differences inside the interval are treated as noise.
- Every grader is code, not an LLM judge. Every failure found so far can be decided by a rule, and code graders are cheap, repeatable and need no calibration. Section 6 shows how the code grader was itself checked against hand labels.
- All results are saved in `report/results/*.json` with every tool call, its arguments and its output, so the scorer can be changed and re-applied without re-running the agent (`--rescore`).

**The paraphrase eval** (`run_tool_eval.py`) passes 61/64 on the final version, the same as V7, so the name-matching change caused no regression.

**The baseline** is the main branch exactly as it was (original prompt and the original 7 tools), run through the same harness. The earlier "Original" row in `prompt_tuning.md` already had the new `list_categories` tool, so it was not a true baseline.

---

## 4. Error analysis: why the agent failed

I read the failed traces by hand and wrote a note for each one (open coding), then grouped the notes into failure modes (axial coding). `eval/analyze_failures.py` applies these codes to any results file. Each failed run gets the code of its **first** failing step, because later errors usually follow from earlier ones.

| Failure mode | What happens | Example (baseline) | Baseline | V7 | Final |
|---|---|---|---|---|---|
| `guessed_id` | Passes a made-up product ID for a product the customer named | "Is the Yoga Mat Premium…" → `get_product_details(product_id=12345)` | 15 | 0 | 0 |
| `no_tool_call` | Asks the customer for an ID instead of looking it up | "How much is the Leather Messenger Bag?" → "Could you provide the product ID?" | 14 | 0 | 0 |
| `invented_syntax` | Makes up query syntax, so the search finds nothing | `search_orders("email:bianca@example.com")` → "no orders found for this email" | 11 | 0 | 0 |
| `data_not_retrieved` | The needed fact is in no tool output (wrong category, no match, or the tool never returns it) | "skincare" → only the category list; existing return without its refund | 7 | 13 | 6 |
| `skipped_write_action` | Return requests never call `initiate_return` | "I want to return order #14" → looks up the order, asks for an email | 6 | 0 | 0 |
| `empty_reply` | No text and no tool call | "What is the status of order #7?" → "" | 3 | 0 | 0 |
| `dropped_fact` | The tool returned the fact, but the reply left it out | One outdoor product missing from a list | 1 | 1 | 1 |
| **Failed runs** (asked-for criteria) | | | **57/105** | **14/105** | **7/105** |

**What this shows:**
- **Baseline failures happened before or at the tool call.** The model either did not call a tool or called it with an invented argument. This is why the V2 prompt (one exact example per tool, an exact-name rule) and the V7 tools (accept product names) removed four whole failure modes.
- **`invented_syntax` explains a gain the earlier report did not explain.** order_lookup went from 20/32 to 32/32 facts under V2. The cause: the baseline model wrote `"email:x@example.com"` instead of the plain email, the search returned nothing, and the agent told a real customer they had no orders. V2's plain-email example fixed it.
- **The remaining failures are retrieval failures, not reasoning failures.** "Fitness equipment" goes to the Electronics category in 2 of 3 runs, and "skincare" does not map to Beauty. Both are fixable in the tools (section 8).

---

## 5. What changed and why

### 5.1 Changes (details in `prompt_tuning.md`)

| Change | Failure mode it targets | Evidence |
|---|---|---|
| Prompt: one question → tool-call example per tool, exact tool names, "never guess an ID" (V2) | `no_tool_call`, `invented_syntax`, `empty_reply` | 76 → 89 facts; empty replies traced to invented tool names (`prompt_tuning.md` Step 6) |
| New `list_categories` tool with keyword matching and fallbacks (V4–V6) | `data_not_retrieved` on "what do you sell?" questions | Book questions 0/12 → 12/12 (section 4.4) |
| `get_product_details` and `check_inventory` accept a name, not just an ID (V7) | `guessed_id` | Prompting to chain worked 2/60 times; name-accepting tools 48/48 (section 5) |
| `initiate_return` reports an existing return's reason and refund (this round) | `data_not_retrieved` on returns | The tool never returned the refund the expected answer needs. Returns 6/12 → 12/12 |
| Product names match whole words and flag near-misses as "No exact match" (this round) | Wrong-entity answers caused by the V7 name matching | "Nike Air Max" matched "Hair Clip Set"; "Kettlebell 50lb" returned the 25lb one as if it were the same. Unit tests cover both |
| Session memory, opt-in per thread (this round) | Follow-up turns lose context (the prompt says "ask for the email", but the next turn forgot the question) | Section 5.3 |

**Why the near-miss label matters:** V7 fixed guessed IDs by letting tools resolve names. However, fuzzy resolution moved the same risk into the tool: for a product we don't sell, the tool returned a different product, and the agent presented it as the one asked about. The tool now says "No exact match for 'X'. Closest products (not the same item…)".

### 5.2 Held-out scenarios

The 35 queries and the paraphrase set were used to choose between versions, so their scores are optimistic. I built a separate set to check that the gains carry over.

- **How it was built** (`eval/build_scenarios.py`): each scenario is a tuple of four dimensions, chosen from the failure modes above. The dimensions are the intent, how the entity is named (ID, exact name, partial name, email, none, nonexistent), the data state (normal, pending, return exists, not sold, not found), and phrasing (formal or casual). Expected values come from SQL, so there are no hand-written answers to get wrong. No entity overlaps with the other eval sets or the prompt's examples.
- **It was run once on the final version and once on the baseline.** Nothing was tuned on it.

Results after correcting two over-strict checks in my generator, applied to both systems by re-scoring the saved runs. The partial-name check now looks for the stock count, not the full product name. The casual "tracking pls" question no longer requires the carrier. Before the correction: baseline 62/86 (72%), final 68/86 (79%).

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
| casual / formal phrasing | 26/38 / 34/48 | 32/38 / 42/48 |

**How to read this:** the final version wins where the baseline had to turn a name or an email into a tool call. It is no better on ID-based questions, which the baseline already handled, and it is worse on questions it should decline.

**New failures it found** (read by hand):
- **Invented rankings, 4/4.** "whats ur top rated running shoe" → "One of the top-rated running shoes is the Blue Ultraboost…". The data has no ratings. The baseline said "I don't have enough information to determine which… has the best reviews" in 2 of 4 runs, so this is a regression. A likely cause is the final prompt's "get facts only by calling a tool" rule with no rule for what to do when no tool can answer.
- **Casual stock questions go to the wrong tool.** "hey do u have any Corduroy Overalls left? how many" → `list_categories`, which has no stock counts. One reply then invented "1 unit available" (caught by the groundedness check).
- **A pending order's return** was handled with a lookup only, and the reply never said the order cannot be returned yet.
- **Scorer false fails, 6 runs**, corrected above. My generated checks were too strict in two places: the full product name for partial-name questions ("The Canvas Tote is in stock, 200 units" is correct), and the carrier for "tracking pls" questions.
- **A scorer false pass.** "can you show me all my orders?" passes because the reply asks for an email. However, it asks only after searching for an invented one (section 5.4).

**Disclosure:** while building the name-matching fix, I viewed the tool output for three partial names that are also in this set ("Black Leather", "Canvas Tote", "Fleece Zip-Up"), as a check after the fix. Nothing was changed because of them. The not-sold names I probed during the fix were swapped for new ones before the run.

### 5.3 Session memory

`Agent.run` used to start a new conversation on every call, so a two-turn exchange ("show my orders" → "which email?" → "karen@example.com") lost the question. The graph now takes a LangGraph `MemorySaver` checkpointer, and runs that share a `thread_id` form one conversation. It is opt-in (`Agent(memory=True)`). The chat CLI uses one thread per session, and the single-turn evals are unchanged.

| Session | No memory | Memory |
|---|---|---|
| Missing email, then given | 3/3 | 3/3 |
| Return without an order number, then given | 1/3 | **3/3** |
| Product follow-up with a pronoun ("how much does it cost?") | 0/3 | **3/3** |
| Order follow-up ("who is shipping it?") | 0/3 | **3/3** |
| Customer corrects the product | 3/3 | 3/3 |
| No leak between two customers' sessions | 3/3 | 2/3 |
| **All** | 10/18 (56%) | **17/18 (94%)** |

- **The sessions that need context go from 1/9 to 9/9.** Without memory, "how much does it cost?" gets "which product?", and "who is shipping it?" gets an answer about a **different order the model made up** (#22 or #44, both IDs from the prompt's examples).
- **Two sessions do not test memory.** "Sure, it's karen@example.com" and "Sorry, I meant the Canvas Slip-On Sneakers" can be answered without the first turn, so they pass either way. Future follow-ups should depend on the earlier turn.
- **The one failure with memory is not a memory leak.** The other customer's data did not cross threads. Instead, the new session's "show me my orders" made the agent invent an email (section 5.4).

Memory does **not** fix tool chaining. Chaining fails *within* one turn, where the ReAct loop already has every message. Memory only carries context *across* turns.

### 5.4 Release blocker: prompt examples used as defaults

The multi-turn isolation check found this. I then reproduced it 12 times with "Show me my orders please." and similar questions, recording the tool calls.

| What the agent did | Runs |
|---|---|
| Asked the customer for their email first | **0/12** |
| Searched an invented placeholder (`your@example.com`, `user@example.com`, …), then asked | 9/12 |
| Searched **`grace@example.com`**, the email in the prompt's example, and **listed Grace Kim's orders** | **3/12** |

- **This is a privacy failure.** One customer sees another customer's orders, names and totals. The prompt already says "If they did not give one, ask for it", but the model ignores it.
- **It is a pattern, not a one-off.** Without memory, a follow-up about "it" was answered with order #22 or #44, which are also the prompt's example IDs. When the customer leaves out an entity, the 3B model fills it in from the prompt's examples.
- **No eval caught it before.** The 35 queries always give the email, and the fact scorer only checks what the reply contains. Catching it needs a check on tool **arguments**: the email passed to `search_orders` must appear in the customer's messages.

---

## 6. Checking the scorer

A code grader can be wrong too, so I checked it against hand labels. I sampled 40 runs (20 baseline, 20 final, mixing scorer passes and fails), read each reply, and labelled it pass or fail as a support lead would. The labels and notes are in `report/results/label_audit.csv`.

| Scorer | Failures caught (TPR) | Good replies passed (TNR) | Agreement |
|---|---|---|---|
| Strict key facts (from `expected_answer`) | 13/17 (76%) | 16/23 (70%) | 72% |
| **Asked-for key facts** | 12/17 (71%) | **21/23 (91%)** | **82%** |

**What the audit found:**
- **The strict scorer fails correct answers.** The expected answers include details the customer did not ask for, such as a tracking number for "what carrier… and when will it arrive?" or prices for "do you sell sunglasses?". So I added an **asked-for** view (`ASKED_FOR` in `run_fact_eval.py`). For 11 queries, it checks only what the question asks, with the reason noted beside each one. Both views are reported, so nothing is hidden.
- **Both scorers miss mislabelled dates**, the most common failure they miss (4 of the 5 missed failures). `search_orders` prints the order date in brackets with no label, so the agent writes "Order #47: Cancelled… delivered on 2026-04-10". That is the order date, and the order was never delivered. No fact check can catch this. It is why order_lookup's 15/15 overstates quality, and it is next step 2.
- **Limits:** one reviewer (the labels are mine and should be confirmed by the domain expert), 40 samples, and the same sample was used to design the asked-for view. A fresh sample is needed to confirm the 91%.

---

## 7. Problems found in the dataset

- **Unreachable facts.** Queries 18 and 31 expect the refund of an existing return, but the original `initiate_return` never returned it. No agent could pass them. They now pass, after the tool fix.
- **A contradiction.** Query 18 says the boots came in the "wrong color", but the existing return #2 says "sole separated after one hike". The expected answer reports the existing return, which is right, but the query and the data disagree.
- **A mislabelled category.** Query 13 ("when was order #8 placed and what was in it?") is labelled `order_status`, but it is an order-details question.
- **Seed dates.** `customers.created_at` and `returns.created_at` are set when the seed script runs, so every return is filed months after delivery (`prompt_tuning.md` section 2).

---

## 8. Next steps, in priority order

1. **Never show one customer another customer's data (section 5.4).**
   - Replace the prompt's example entities with ones that do not exist in the store (an email and order IDs with no rows).
   - Add a deterministic guardrail in the graph: before `search_orders` runs, check that the email appears in the customer's messages, and otherwise ask for it. This is a fast, explainable code check of the kind that belongs in the request path, not an LLM judge.
   - Add the argument check to the evals, and add "my orders" and "my last order" cases with no entity given.
   - This is first because it is the only failure that harms a third party, and the prompt rule alone does not prevent it.
2. **Stop invented claims on questions the data cannot answer.** Out-of-scope questions fell from 2/4 to 0/4, and inventing a "top-rated" product misleads customers. Add a prompt rule ("we have no ratings or reviews; say so"), add 10–15 held-out cases (ratings, delivery promises, discounts), and gate on them.
3. **Label dates in tool outputs, and add a check for date labels.** `search_orders` and `lookup_order` print bare dates, and the agent calls them shipping or delivery dates. The fix is to print "ordered 2026-04-10" and to show `shipped_at` and `delivered` only where they exist. Then add a code check that flags "shipped/delivered on <date>" when the date is the order date. This matters because the fact scorer cannot see this error, so a 100% order_lookup score hides it.
4. **Fix catalog retrieval for stock and category questions.** These cause the remaining failures on both sets: "fitness equipment" → Electronics, "skincare" with no synonym, casual "how many left" questions sent to `list_categories`, and category listings without stock counts. Options: include stock counts in `list_categories`, add a small synonym map, or split it into `list_categories()` and `list_products(category)`, so that neither has an optional argument. Measure each option on the tool eval and held-out set separately.
5. **Grow the eval set from real use, and keep looking at traces.** Once there is traffic, sample real conversations every week, repeat the open and axial coding, and add each new failure to the CI set. The synthetic scenarios are templates, so real phrasing will find failures they miss. Add an LLM judge only for criteria that code cannot check (such as a helpful decline), and only after 100+ labelled examples to measure its agreement.

**Deliberately not prioritized:**
- **A separate order-lookup agent (multi-agent routing).** Order intents already pass 10/10 on the held-out set and 15/15 on the 35 queries. A router would add a new failure point (wrong routing) without a failure that needs it. I would test it only as a hypothesis, "a router that narrows the toolset improves tool choice on this 3B model", if step 3 does not fix tool selection.
- **Tone-based personas.** Phrasing is already a scenario dimension (casual 28/38 vs formal 40/48), and the casual gap comes from tool choice, not tone. More personas are worth adding only if trace review shows tone changes the outcome.

---

## Appendix: reproducing the results

```bash
poetry run python -m unittest discover tests
poetry run python -m eval.run_fact_eval --runs 3 --out report/results/fact_eval_v8.json
poetry run python -m eval.analyze_failures report/results/fact_eval_baseline.json report/results/fact_eval_v8.json
poetry run python -m eval.run_scenario_eval --runs 2 --out report/results/scenarios_v8.json
poetry run python -m eval.run_multiturn_eval --runs 3 --out report/results/multiturn_memory.json
poetry run python -m eval.run_multiturn_eval --runs 3 --no-memory --out report/results/multiturn_no_memory.json
```

The baseline was run by extracting the main branch (`git archive 029ffaf src`) into a separate folder, adding the same `eval/` files, and running the same commands there.
