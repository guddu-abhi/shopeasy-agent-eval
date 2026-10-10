# Error Analysis of the Baseline Agent (main branch)

This report applies the error-analysis process from Hamel Husain and Shreya Shankar's [LLM Evals FAQ](https://hamel.dev/blog/posts/evals-faq/) to the unmodified `main` branch agent (`qwen2.5:3b`, 7 tools, 5-line system prompt). The goal is to find out *how* the agent fails, how often, and what to fix first. It does not change the agent.

## 1. Summary

- **The baseline passes 57 of 141 traces (40%).** On the 35 original eval queries, it passes 41 of 105 runs (39%). On 12 new edge-case queries, it passes 16 of 36 runs (44%).
- **Three failure modes cause 56% of the 84 failures.**
  1. **The agent invents IDs instead of searching (26%).** For example, it calls `check_inventory(12345)` or `check_inventory(123)` for a product the user named, or `lookup_order(12345)` for a user who gave an email.
  2. **The agent asks the user for information it could look up (18%).** For example, it asks for a product ID, or for an order number the user already gave.
  3. **The agent invents query syntax (12%).** For example, it calls `search_orders("email:bianca@example.com")`, gets no match, and tells the customer it couldn't find any orders. Bianca has 3 orders.
- **The next two modes add 17%.** The agent looks up the order but never acts on a return request (8%), or it returns an empty answer (8%).
- **Questions that name a product pass only 4 of 27 times (15%).** Questions that give an order ID pass 38 of 63 times (60%).
- **About half of failures (41 of 84) tell the customer something false or unsupported.** Examples include "the hammock is not in stock" (it has 70 units), "no orders found" (there are 3) and an invented "30-day return policy". In 11 traces, the agent presents the order date as a delivery or ship date.
- **The current eval cannot measure these failures reliably.**
  - It has no scoring and no tool-call logging.
  - One query can write to the real database.
  - Several reference answers need data the tools never return.
  - 17 of 47 queries got different pass/fail results across 3 runs of the same input, so comparing two agent versions on a single run is unreliable.

## 2. Method (following the guide)

| Guide step | What I did, and where it falls short of the guide |
|---|---|
| **Collect traces** | I ran the main-branch agent on all 35 eval queries, plus 12 synthetic edge cases, 3 times each, for **141 traces from 47 distinct queries**. I logged every message, tool call, tool result and latency. Each trace ran on a fresh copy of `store.db`, so `initiate_return` never changed the real DB. I confirmed that the Python sources, eval and `store.db` match the main commit (`029ffaf`). **Shortfall:** the guide says to "start with 100 diverse traces". The repeats show run-to-run variation, but they do not add input diversity. The guide does not discuss repeated runs; that part of the design is mine. |
| **Synthetic data** | The 35 eval queries are mostly "happy path". Before running anything, I wrote 12 extra queries. They vary three dimensions: **data state** (not found, return blocked by order status, not shipped), **request shape** (two questions in one, missing ID, out of scope) and **input variation** (upper-case email). I wrote the expected behaviour for each from the DB before running it. **Shortfall:** I wrote the queries directly. I did not use the guide's two-step method (write dimension tuples first, then turn each tuple into a query). |
| **Open coding** | I read every trace and wrote a note on the **first upstream failure**, as the guide recommends. My first-pass viewer cut off long tool results and answers. Later passes re-read all 141 traces in full, and changed 8 labels from pass to fail (see the revision note in section 8). I recorded a few notable downstream errors as secondary codes, but I did not code downstream errors systematically. |
| **Binary pass/fail** | A trace **passes** if the answer gives the facts the user asked for, matches the DB, makes no false or invented claims, and completes any requested action. Detail beyond what the user asked for is not required. For example, a price question passes without the product description. I wrote this rubric *after* reading traces, as the guide advises. |
| **Axial coding** | I grouped the notes into 11 failure modes (section 3) and counted them. |
| **Slices and root causes** | I computed pass rates by eval category, by how the user refers to the entity, and by run-to-run consistency. I looked for causes only after counting (section 5). |

**Caveats**

- **I, an AI assistant, did the open coding.** The guide recommends a domain expert as the "definitive voice on quality standards" (the benevolent dictator). It also says to annotate "at least 30 traces yourself before reviewing suggestions from an agent". **The labels in `error_analysis_data/labels.csv` should be reviewed by the project owner** before anyone builds evaluators on them. The 11 close calls that I still passed have `outcome` set to `borderline`.
- **Counts describe this test set, not real traffic.** The queries are curated and partly synthetic, so a failure mode's share here does not show how often real customers would hit it.

## 3. Failure taxonomy

These are first-failure counts over the 84 failing traces.

| Code | Failure mode | Count | Share | Queries affected |
|---|---|---:|---:|---|
| **A** | **Invents an ID instead of searching.** The agent calls an ID-based tool with a made-up ID (`12345`, `123`, `123456`). | **22** | 26% | 1, 7, 8, 11, 28, 32, S8, S11 |
| **B** | **Asks the user instead of looking it up.** The agent makes no tool call and asks for a product ID, brand or "what kind of gear". Sometimes it asks for the order ID the user just gave. | **15** | 18% | 10, 16, 22, 24, 35, S2, S3, S4 |
| **D** | **Invents query syntax.** The agent passes `email:…`, `category:…` or `… AND …` to a search tool that only does plain matching. | **10** | 12% | 20, 22, 27, 30 |
| **F** | **Return action not executed.** The agent looks up the order but never calls `initiate_return`. It then asks for details or confirmation, or tells the user to do it. | **7** | 8% | 4, 23, 31, S2 |
| **C** | **Empty response.** The final message is an empty string, with no tool call. | **7** | 8% | 9, 17, 18, S1, S10 |
| **L** | **Calls the order date a ship or delivery date.** For example, it says "delivered on 2026-01-18" when that is the date the order was placed. It is the first failure in 6 traces. It also appears as a secondary error in 5 more: after an F failure in 4 (Q4, Q23, Q31) and after a J failure in 1 (Q7). | **6** | 7% | 7, 13, 15, 25, 34 |
| **H** | **Invents policy or facts.** Examples are a "30-day return policy", a "refund to your original payment method" and a "return tracking number provided upon approval". None of these appears in the data. | **5** | 6% | 4, 18, S9 |
| **E** | **Search term misses catalog vocabulary, with no retry.** For example, "fitness equipment" and "skincare" match no product name or category. The agent gives up after one empty result. | **4** | 5% | 5, 27 |
| **J** | **Misreads tool output (other than dates).** For example, it swaps two orders' statuses, says "in transit" for "out for delivery", or calls an approved return "complete". | **4** | 5% | 6, 7, 12, 31 |
| **K** | **Tool rejects valid input.** `search_orders` uses a case-sensitive exact match, so `Alice@Example.com` finds nothing. | **3** | 4% | S12 |
| **I** | **Stops mid-chain.** The agent finds the product ID, then asks the *user* to "proceed with using the `check_inventory` tool". | **1** | 1% | 21 |

**Secondary failure G: a false statement built on a wrong tool result.** This happened in 4 traces, all downstream of A. In each, the agent calls `check_inventory(123)`, receives the *Insulated Cooler Bag*, and answers as if it were the requested product:

> "I'm sorry, but the Lightweight Hammock is not in stock at the moment. We currently have the Insulated Cooler Bag 24-Can…" *(Q32. The hammock has 70 units.)*
>
> "We currently have 80 Portable Phone Chargers in stock… the product ID for the Portable Phone Charger is 123." *(Q8. The real figure is 200.)*

### Where in the agent loop the first failure happens

For agents, the guide suggests a *transition failure matrix*: "rows represent the last successful state and columns represent where the first failure occurred." The table below is a simplified version. It records only the step where the first failure happened.

| Step where the first failure occurs | Codes | Fails | Share |
|---|---|---:|---:|
| 1. Deciding to use a tool | B | 15 | 18% |
| 2. Building the tool arguments | A, D | 32 | 38% |
| 3. Retrieval returns the needed data | E, K | 7 | 8% |
| 4. Chaining a second call or taking the action | F, I | 8 | 10% |
| 5. Answering faithfully | J, L, H | 15 | 18% |
| Unknown (empty output, cause not yet diagnosed) | C | 7 | 8% |

- **In 61 of 84 failures (73%), the model never received the data it needed.** It made no tool call (B, C), sent wrong arguments (A, D), or the search returned nothing (E, K). This is where most failures start.
- **Answering from the data is a real second problem (18%).** In 12 of these 15 traces, the agent had the right data, then misread it or added invented facts. Six of those 12 mislabel the order date. In the other 3 (the three runs of S9), no policy data exists and the agent invented a policy.

### What the customer experiences

- **41 of 84 failures (49%) state something about orders, products, stock, returns or policy that is false or not supported by any data.** By first-failure code, they come from D (9), L (6), A (5), H (5), F (5), E (4), J (4) and K (3). The list is in `FALSE_CLAIM` in `labels.py`. I treat these as the most harmful failures, because the customer has no reason to doubt them.
- **The other 43 failures are unhelpful but contain no such claim.** These include asking for an ID, empty replies and unfinished returns.
- **Of the 28 traces with no tool call at all, only 3 passed.** All 3 were "Where is my order?", where asking for an order number is the correct move.

## 4. Slices

### By how the user refers to the entity

| Reference | Pass rate | Main failure |
|---|---|---|
| Product **name** | **4/27 (15%)** | A: invented ID (18) |
| Category / browse | 4/18 (22%) | B: asks instead of searching (6), D (4), E (4) |
| Email | 7/24 (29%) | D: `email:` prefix (6), A (4), K (3) |
| Order ID | 38/63 (60%) | F: return not executed (7), C: empty (5), L: date mislabel (4) |

**Observation:** the agent called `search_products` first in only 5 of the 27 product-name traces. Those 5 passed 4 times (Q21 runs 1–2, Q35 runs 1–2). The sample is small, but it suggests that the existing tools can answer these questions when the agent searches first.

### By eval category (original 35 queries only)

| Category | Pass rate | Main failure |
|---|---|---|
| product_search | 1/12 (8%) | B, D |
| inventory | 2/18 (11%) | A |
| returns | 2/12 (17%) | F, H |
| product_info | 3/12 (25%) | B, A, C |
| order_lookup | 5/15 (33%) | D |
| order_status | 5/9 (56%) | C |
| order_details | 9/12 (75%) | L |
| shipping | 14/15 (93%) | J (1) |

### Run-to-run consistency

- **Passes out of 3 runs:**
  - 0/3: 20 queries
  - 1/3: 7 queries
  - 2/3: 10 queries
  - 3/3: 10 queries
- **17 of 47 queries got different results across runs of the same input.** To compare agent versions, each query needs several runs.
- **The 20 queries that fail in all 3 runs are the most stable signal.**
  - A (invented IDs) is the failure in every run for 7 of them.
  - D is the most common failure for 4, B for 3, and F for 2.
  - The remaining 4 have mixed or single-mode failures.

## 5. Likely root causes

These are hypotheses, formed after counting and checked against the code in `src/agent/`. None has been confirmed by an experiment yet.

| Failure | Likely cause in the code |
|---|---|
| **A, B, I** (product names) | `check_inventory` and `get_product_details` accept only an integer `product_id`. Their docstrings ("Check product availability", "Get information about an item") never say the ID comes from `search_products`. The system prompt gives no workflow. The model then fills the required integer with a placeholder. |
| **D** (invented syntax) | `search_orders(query: str)` is documented as "Find orders matching the query", but the SQL is `WHERE c.email = ?`. The argument name and docstring invite search-engine syntax. `search_products(query)` has the same vague docstring. |
| **E, K** (brittle retrieval) | `search_products` matches the whole phrase against the name or category with one `LIKE '%phrase%'`. It does no word splitting, plural handling or synonyms ("skincare" vs. category `Beauty`), and no tool lists the category names. Email matching uses SQL `=`, which is case-sensitive in SQLite by default. |
| **F** (returns) | `initiate_return` is described as "Handle a customer issue with an order. Use this when a customer has a problem." It never says that it *creates a return* or that it reports existing returns. In all 7 F traces, the agent called `lookup_order` and then handed control back to the user. |
| **L** (dates) | The tool outputs label the order date only as `Date:` (`lookup_order`), or not at all (`(2026-03-25)` in `search_orders`). Nothing says it is the date the order was placed. |
| **H, J** (grounding) | The prompt never says to state only facts returned by tools, and no tool holds policy information. |
| **C** (empty output) | **Not yet known.** All 7 traces contain only the user message and one empty AI message. Diagnosing this needs the raw model output, which the harness does not log. |

**Product and design gaps.** These are not model errors, but the guide says to record them because they affect users.

- The agent has no identity check. Anyone can list a customer's orders by email, or see a customer's name and email from an order ID. In one trace, the agent offered "you can reach out to her at carol@example.com".
- The agent has no access to policy information, such as return windows or refund methods.

## 6. Problems with the current eval itself

1. **No scoring and no traces.** `eval/run_eval.py` prints only the final text. The most common failures here are argument errors (A and D, 32 of 84, or 38%). Only the tool calls reveal these, and the eval does not show tool calls.
2. **The eval can write to the real database.** When the agent calls `initiate_return` for Q4 (1 of 3 runs here), it creates a real return in `store.db`. On later runs, the correct answer becomes "a return already exists", which no longer matches the reference.
3. **Some references require data that the tools never return.**
   - **Q18, Q23 and Q31** expect the *reason* of an existing return, and Q18 and Q31 also expect the refund amount. However, `initiate_return` only returns `Return #id, status`.
   - **Q5** expects unit counts for individual fitness products and a total of 15. `search_products` returns no stock, so this needs one `check_inventory` call per product.
   - **Q9** expects shipping details *and* items, which needs two different tools.

   As a result, a perfect agent would still miss facts on these queries.
4. **Q16's reference is incomplete.** The catalog has two sunglasses (#16 and #78), but the reference lists one.
5. **Coverage is mostly happy-path.** Q18, Q23 and Q31 test returns that already exist. However, none of the 35 queries covers a missing order or email, a return blocked by order status, an out-of-scope question or a case variant. The synthetic queries exposed two failure modes the original set never triggered: K (case-sensitive email) and B's "asks for the order ID it was just given".
6. **There is one run per query.** This is not enough, because 17 of 47 queries got different results across runs.

## 7. Recommended next steps, in priority order

The guide says to "fix these obvious gaps first before building complex evaluation infrastructure". It also says to "favor assertions or other deterministic checks over LLM-as-judge evaluators". The order below follows frequency, plus a judgment of how much each failure hurts the customer.

1. **Fix ID invention and product-name resolution (A, I, and B on product names; 27 traces).**
   - **Fix:** let `check_inventory` and `get_product_details` accept a product name, or describe the search-first workflow explicitly in the docstrings and prompt.
   - **Evaluator (code, no LLM):** check that every ID argument appears in the user message or in an earlier tool result.
   - **Tested on these traces:** of the 81 tool calls that pass an ID, the check flags exactly the 22 code-A traces and nothing else. It is implemented at the end of `labels.py`.
2. **Make the search tools tolerant of what the model sends (D, E, K; 17 traces).** 16 of these 17 end in a false "nothing found".
   - **Fix:** strip `email:` and `category:` prefixes, lower-case emails, match keywords individually and against category names, and state the expected input format in the docstrings.
   - **Evaluator (code):** check that `search_orders` receives a bare email, and that the final answer contains the expected order IDs.
3. **Decide the returns policy, then align the agent (F; 7 traces).** Should the agent create a return immediately, or confirm first? This is a product decision for the benevolent dictator. The current references assume immediate creation.
   - **Then:** rewrite the `initiate_return` docstring, and make the tool report the reason and refund amount of an existing return.
   - **Evaluator (code):** for return requests, check that `initiate_return` was called.
4. **Fix the eval harness before measuring any improvement.**
   - Score each run against key facts with code (IDs, amounts, statuses, tracking numbers).
   - Log full traces.
   - Give each query a fresh copy of the DB.
   - Run each query at least 3 times. This is my recommendation, based on the flakiness measured here. The guide does not cover it.
   - Fix the references listed in section 6 and add the 12 edge-case queries.
5. **Label the dates in the tool outputs (L; 11 traces including secondary).** Write "Order placed: …" instead of a bare date in `lookup_order` and `search_orders`. This is a small code change. Recheck the result with a code-based fact check.
6. **Investigate empty responses (C; 7 traces, 5% of all traces).** Log the raw Ollama output to find the cause. A check that the answer is not empty is a cheap guardrail in the meantime.
7. **Address invented or misread facts (H, J, G; 14 traces, including 4 secondary G and 1 secondary H).**
   - **Fix:** add a prompt rule to state only facts that come from tools.
   - **Evaluator (LLM judge), only if failures persist:** a judge for this one failure, "states a fact not supported by tool output". The guide recommends "a separate judge for each type of failure". Validate it against human labels, reporting TPR and TNR on a held-out set, before trusting it.

**Saturation has not been reached.** The guide says to continue "until new traces stop revealing failure modes or changing existing ones". Here, the synthetic batch revealed a new mode (K), and re-reading the traces revealed another (L). Multi-turn conversations, vague references ("my last order") and adversarial inputs are untested. After the fixes above, the next round should collect at least 100 fresh traces from more diverse inputs.

## 8. Reproducing this analysis

All evidence is in `report/error_analysis_data/`.

- **`collect_traces.py`** reruns the 141 traces against the agent, with a fresh DB copy for each trace. Run it from the repo root with `poetry run python report/error_analysis_data/collect_traces.py "$PWD" traces.jsonl 3`.
- **`traces.jsonl`** holds the raw traces used here: every message, tool call, tool result and latency.
- **`label_data.py`** holds the hand labels (first-failure code, secondary code, false-claim flag and note for every trace).
- **`labels.py`** joins the labels with the traces, recomputes the counts in this report and runs the ID-grounding check. Run it with `python3 report/error_analysis_data/labels.py report/error_analysis_data/traces.jsonl`. Add `report/error_analysis_data/labels.csv` as a second argument to rewrite the CSV. A few figures, such as which tools ran in the F traces, come from the `tool_calls` column of `labels.csv`.
- **Run numbering:** runs are numbered 0–2 throughout, matching the `rep` column.
- **`labels.csv`** is the flat label table, intended for owner review. Each row is one trace, and the columns read left to right:
  - **The question:** `id`, `rep`, `category`, `ref` (how the user names the entity) and `query`.
  - **What the agent did:** `tool_calls`, with arguments, and `answer`, its final reply.
  - **The truth:** `db_truth` summarises the matching rows in `store.db`.
  - **The verdict:** `outcome` (`pass`, `borderline` or `fail`), `failure` (the first-failure code, plus a secondary code after `+`, as in `F+L`), `false_claim` and `note`.
  - **The check:** `db_query`, the SQL that returns the `db_truth` rows.
- **`db_facts.py`** holds that SQL for each query and builds those two columns. `trace_store.py` is the trace loader shared by the scripts.
- **`view.py`** is a compact trace viewer for reading traces. It cuts long text, so read the JSON when a label depends on the full answer.

The model is not deterministic, so a rerun will give different counts. A rerun has not been done to test whether the ranking of failure modes holds.

**Revision note.** A second labelling pass, which re-read every passing answer in full, changed these 8 traces from pass to fail:

- **L (order date called a delivery or ship date):** Q7 run 1, Q15 run 1, Q25 runs 1–2 and Q34 run 2.
- **J (approved return called "complete"):** Q31 run 1.
- **H (invented refund method or return tracking):** Q4 run 1 and Q18 run 2.

The pass rate fell from 46% to 40%. A third pass re-read all 84 failing traces in full. It changed no pass/fail label. However, it found the order-date error in 4 F traces (Q4 runs 0 and 2, Q23 run 0, Q31 run 0), which raised the false-claim count from 37 to 41. The second pass also corrected several unsupported statements in the earlier draft:

- The earlier draft quoted a `get_product_details(123)` call that never happened.
- It said answering from correct data was nearly always right, which is not true.
- It called the step table a transition matrix.
- It said the edge-case queries were written while reading traces. They were written before any run.

The third pass also corrected these:

- The report said 73% of failures are visible only in tool calls. Empty and "asks the user" replies are visible in the final text, so the claim now covers only argument errors (38%).

**Consistency check.** A static check compared these files with each other and with `store.db`, without rerunning the agent. All 117 recorded tool results matched a replay of the same calls on a fresh copy of `store.db`, and all 141 final answers were re-read against the database. The check changed no pass/fail label, first-failure code or false-claim flag. It made these corrections:

- Q7 run 2 also calls order dates ship and delivery dates, so it now has a secondary L. The order-date count rose from 10 to 11.
- S7 runs 1 and 2 give the same status-only answer as run 0, so they are now marked `BORDERLINE` too. The borderline count rose from 9 to 11.
- The note for Q8 run 1 now says why it is a false claim: the agent says no product #123 exists, but #123 is the Insulated Cooler Bag.
