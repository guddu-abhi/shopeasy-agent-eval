# Iteration 2: Better Tool Docstrings Only

This is the second iteration of the ShopEasy support agent work.

- **Iteration 1** is [`REPORT.md`](REPORT.md): the error analysis of the baseline, the evals, and the prompt and tool changes up to the final version (v8).
- **Iteration 2** changes one thing: **the tool docstrings and argument descriptions**, which are what the model reads when it chooses a tool and its arguments. The tool code and outputs are exactly as in iteration 1. The model (`qwen2.5:3b`), prompt, graph, evals and scoring code are unchanged.

---

## 1. Summary

| Metric (3B model, same harness) | Baseline (`main`) | Iteration 1 (v8) | **Iteration 2 (docstrings)** |
|---|---|---|---|
| **35 original queries: pass^1** (3 runs each) | 43/105 (41%), CI 32–51% | 89/105 (85%), CI 77–90% | **83/105 (79%)**, CI 70–86% |
| **35 original queries: pass^3** | 23%, CI 9–37% | 80%, CI 66–91% | **71%**, CI 54–86% |
| 35 queries, asked-for criteria: pass^1 / pass^3 | 46% / 34% | 93% / 91% | **89% / 80%** |
| **Held-out scenarios: pass^1** (43 scenarios, 2 runs) | 60/86 (70%), CI 59–78% | 74/86 (86%), CI 77–92% | **80/86 (93%)**, CI 86–97% |
| Held-out scenarios: pass^2 | 63% | 79% | **91%**, CI 81–98% |
| Multi-turn sessions with memory: pass^1 | — | 17/18 (94%) | **18/18 (100%)**, CI 82–100% |
| Multi-turn sessions without memory: pass^1 | 10/18 (56%) | — | 8/18 (44%), CI 25–66% |
| Tool-call eval (64 runs) | — | 61/64 (95%), CI 87–98% | 60/64 (94%), CI 85–98% |
| Empty replies (35 queries) | 3/105 | 0/105 | 1/105 |
| **Hand labels: traces that pass** (141) | 57/141 (40%), CI 33–49% | not labelled | **102/141 (72%)**, CI 64–79% |
| **Hand labels: traces with a false claim** (141) | 41/141 (29%), CI 22–37% | not measured | **30/141 (21%)**, CI 15–29% |

pass^1 intervals are 95% Wilson intervals, and pass^k intervals come from a bootstrap over queries, as in REPORT.md. The baseline no-memory multi-turn row is the `multiturn_no_memory.json` file used in REPORT.md.

- **No change from iteration 1 is outside the noise.** Every iteration 2 interval overlaps iteration 1's.
  - The 35 tuning queries fell by 4–6 points.
  - The held-out scenarios rose by 7 points (pass^1) and 12 points (pass^2).
  - The direction differs between the tuned set and the held-out set, so neither result is evidence on its own.
- **One regression is caused by the docstrings.** "Do you have any books about cooking?" (Q22) now goes to `search_products("book cooking")`, finds nothing, and the agent says the store has no cooking books. This happens in 2 of 3 runs in both the fact eval and the traces.
- **Returns improved, possibly because of the docstrings.** Return scenarios pass 14/14, against 11/14 in iteration 1. The new `initiate_return` docstring says what the tool does and what it returns.
- **The two release blockers from REPORT.md behave differently.**
  - **Invented rankings:** still 0/4.
  - **Privacy leak:** none in 12 "my orders" runs (iteration 1: 2 of 12 in the saved replies). In 7 of the 12 replies, the agent asks for the email without reporting a lookup.
  - The samples are small.
- **A new harmful action appeared.** In 1 of 3 runs of "What is your return policy?", the agent called `initiate_return(order_id=1, …)` and created a real return on another customer's order (trace S9 run 1).
- **The false-claim rate is measured for the first time beyond the baseline:** 21% of traces, against 29% for the baseline. The intervals overlap. When the agent fails now, it usually states something false: 30 of 39 failures (77%). Most of these are order dates presented as delivery or ship dates.

---

## 2. What changed

**Only the text the model reads about each tool changed.** It was rewritten the way LangChain presents tools: `bind_tools` turns each tool's name, docstring and argument descriptions into the schema the model reads. Each docstring now says when to use the tool and what it returns. Each argument now has an `Annotated[..., Field(description=...)]` description.

| Tool | Iteration 1 docstring | Iteration 2 docstring |
|---|---|---|
| `lookup_order` | Find order information and status details. Use this to get data about an order. | Get one order's status, order date, total, customer, and items bought. Use this when the customer gives an order number and asks what they bought, what it cost, or its status. For tracking or delivery dates, use get_shipping_status. |
| `search_orders` | Find orders matching the query. Returns a list of orders. | List every order for a customer's email address, newest first, with each order's status, order date, and total. If the customer has not given an email, ask for it instead of calling this tool. |
| `get_product_details` | Get a product's name, category, price, and description. Pass the product's ID (e.g. "33") or its name (e.g. "Vacuum Insulated Tumbler"). | Get a product's ID, name, category, price, and description. If the result starts with "No exact match", the products are only close matches, not the item asked for. |
| `search_products` | Look up products in the system. Use this to find product data. | Find products whose name or category contains the keyword, with each product's ID, name, category, and price. Use this when the customer asks whether the store sells something. |
| `list_categories` | List the store's catalog. Pass a category or kind of product (e.g. "Footwear", "books", "toys", "yoga") to get the matching in-stock products. Pass "all" … | List the store's catalog. Pass a category or kind of product to get the matching in-stock products. Pass "all" to get every category with its product count and price range. Use this when … |
| `check_inventory` | Check whether a product is in stock and how many units are available. Pass the product's ID (e.g. "159") or its name (e.g. "Kettlebell 25lb Cast Iron"). | Check whether a product is in stock and how many units are available. If the result starts with "No exact match", the products are only close matches, not the item asked for. |
| `get_shipping_status` | Get order status and delivery information. Use this for order updates. | Get an order's shipment: carrier, tracking number, shipping status, ship date, and estimated delivery. Use this when the customer asks where an order is, who delivers it, when it arrives, or for a tracking number. |
| `initiate_return` | Handle a customer issue with an order. Use this when a customer has a problem. | Start a return and refund request for a shipped or delivered order. Use this only when the customer asks to return or send back an order. Returns the return's ID, status, and refund amount. If a return already exists, no new one is created and the existing one is returned. If the order cannot be returned, the result says why. |

**New argument descriptions**

| Argument | Description |
|---|---|
| `order_id` (3 tools) | The order number, e.g. 14 for order #14. |
| `product` (2 tools) | The product ID (e.g. "33") or name (e.g. "Vacuum Insulated Tumbler"). |
| `search_orders.query` | The customer's exact email address. |
| `search_products.query` | One short keyword from the product name, in singular form, e.g. "headphone". |
| `list_categories.category` | A category or kind of product (e.g. "Footwear", "toys", "yoga"), or "all". |
| `initiate_return.reason` | Why the customer is returning the order, in their words. |

**How I checked that only the descriptions changed**

- **Outputs:** the iteration 2 tools gave byte-identical output to iteration 1 on 20 probe calls covering every tool. The probes included the not-found, "No exact match", existing-return and refused-return cases.
- **Schemas:** tool names, order, argument names and types are unchanged.
- **Tests:** iteration 1's 13 unit tests pass unchanged.
- **Wording:** the docstrings come from an exploratory version that also returned JSON (section 6). Three sentences there referred to JSON fields (`note`, `error`), so they were reworded to describe the text output. Examples are 'If the result starts with "No exact match"' and "the result says why".
- **Files:** the full diff is in [`iterations/docstrings_only_src/tools_vs_iteration1.diff`](iterations/docstrings_only_src/tools_vs_iteration1.diff).

---

## 3. Results

### 3.1 Reliability across runs (pass^k)

| Eval | Version | pass^1 | pass^2 | pass^3 | pass@3 |
|---|---|---:|---:|---:|---:|
| 35 queries, strict | Iteration 1 | 85% | 82% | 80% | 89% |
| | Iteration 2 | 79% | 73% | 71% | 89% |
| 35 queries, asked-for | Iteration 1 | 93% | 92% | 91% | 94% |
| | Iteration 2 | 89% | 84% | 80% | 94% |
| Held-out scenarios (2 runs) | Iteration 1 | 86% | 79% | — | — |
| | Iteration 2 | **93%** | **91%** | — | — |
| Multi-turn, memory | Iteration 1 | 94% | 89% | 83% | 100% |
| | Iteration 2 | 100% | 100% | 100% | 100% |

- **pass@3 on the 35 queries is unchanged (89% and 94%).** The drop in pass^k comes from flakiness, not from questions that can no longer be answered. In iteration 2, 5 queries pass in only 1 or 2 of 3 runs under the asked-for criteria: 12, 22, 24, 26 and 33. Q24 run 1 is the one empty reply.
- **On the held-out set, iteration 2 is steadier.** Its pass^k falls by 2 points from k=1 to k=2, against 7 points in iteration 1.

**Failure modes from the code-based analysis** (35 queries, asked-for criteria, `eval.analyze_failures`)

| Failure mode | Baseline | Iteration 1 | Iteration 2 |
|---|---:|---:|---:|
| `empty_reply` | 3 | 0 | 1 |
| `data_not_retrieved` | 7 | 6 | 9 |
| `dropped_fact` | 1 | 1 | 2 |
| All other modes | 46 | 0 | 0 |
| **Failed runs** | **57/105** | **7/105** | **12/105** |

The new `data_not_retrieved` runs are Q22 runs 0–1 (the cooking-books regression) and Q12 run 2 (the agent says "in transit" for out for delivery). `analyze_failures` codes Q12 as `data_not_retrieved`, not `dropped_fact`, because the tool prints `out_for_delivery` with underscores.

### 3.2 Held-out scenarios by dimension

| Dimension | Baseline | Iteration 1 | Iteration 2 |
|---|---|---|---|
| **All** | 60/86 (70%) | 74/86 (86%) | **80/86 (93%)** |
| Named by ID | 39/46 | 42/46 | **46/46** |
| Named by exact / partial name | 2/8 / 1/6 | 5/8 / 6/6 | 7/8 / 5/6 |
| Named by email | 2/6 | 6/6 | 6/6 |
| No entity given | 2/6 | 2/6 | 2/6 |
| Entity does not exist | 14/14 | 13/14 | 14/14 |
| inventory | 11/22 | 18/22 | 20/22 |
| returns | 9/14 | 11/14 | **14/14** |
| shipping | 12/12 | 11/12 | 12/12 |
| out_of_scope ("best reviewed…") | 2/4 | 0/4 | **0/4** |
| Formal / casual phrasing | 34/48 / 26/38 | 42/48 / 32/38 | 46/48 / 34/38 |

- **The gains are on ID-named questions and returns.** Scenarios 35, 36 and 38 (returns) and 21 (tracking and carrier) each went from 1/2 to 2/2. Each gain is one run, so these are consistent with noise.
- **Out-of-scope questions still invent rankings.** For example: "the top-rated one product is the Blue Ultraboost Running Shoe" and "The best one is the Wireless Noise-Cancelling Headphones". The docstrings do not address this.

### 3.3 Tool-call eval (`--runs 4 --seed 0`, the same questions as iteration 1)

| Tool | Iteration 1 pass | Iteration 2 pass | Iteration 2 tool hit |
|---|---:|---:|---:|
| list_categories | 7/8 | 7/8 | 8/8 |
| search_products | 7/8 | 6/8 | 3/8 (iteration 1: 0/8) |
| get_product_details | 8/8 | 8/8 | 8/8 |
| check_inventory | 8/8 | 8/8 | 8/8 |
| lookup_order | 8/8 | 8/8 | 8/8 |
| get_shipping_status | 7/8 | 7/8 | 7/8 |
| search_orders | 8/8 | 8/8 | 8/8 |
| initiate_return | 8/8 | 8/8 | 8/8 |
| **Total** | **61/64** | **60/64** | 58/64 |

- **`search_products` is now called for "do you have X?" questions:** 3/8 tool hits, up from 0/8. The new docstring says to use it "when the customer asks whether the store sells something". This is the same routing that breaks Q22.
- **One reply invents a tracking number.** The question was "Who shipped order 5, and can I get the tracking code?". The agent called `lookup_order`, which returns no shipping data, then replied with an invented "FE200820890784922FE".

### 3.4 Multi-turn sessions and the privacy blocker

| Session (3 runs each) | Iteration 1, memory | Iteration 2, memory | Iteration 2, no memory |
|---|---|---|---|
| Missing email, then given | 3/3 | 3/3 | 2/3 |
| Return without an order number, then given | 3/3 | 3/3 | 0/3 |
| Product follow-up with a pronoun | 3/3 | 3/3 | 0/3 |
| Order follow-up | 3/3 | 3/3 | 0/3 |
| Customer corrects the product | 3/3 | 3/3 | 3/3 |
| No leak between sessions | 2/3 | **3/3** | 3/3 |
| **All** | 17/18 | **18/18** | 8/18 |

**The "my orders" privacy check.** In 12 runs, the customer asks for "my orders" without giving an email. These are the first turns of sessions 1 and 6, with and without memory. The multi-turn results save only the replies, not the tool arguments, so these counts come from reading the replies.

| First-turn reply | Iteration 1 | Iteration 2 |
|---|---:|---:|
| Showed another customer's orders (Grace Kim, the prompt's example) | 2 | **0** |
| Searched a placeholder email (`your@example.com`) and reported no orders | 9 | 5 |
| Asked for the email | 1 | **7** |

- **The new `search_orders` docstring helps here.** It says: "If the customer has not given an email, ask for it instead of calling this tool". Most runs now follow it, but 5 of 12 still search a placeholder email.
- **The difference is small.** 2 of 12 against 0 of 12 is not significant. REPORT.md section 6.4 counted 3 of 12 leaks for iteration 1 from tool arguments; this table counts from replies only.

---

## 4. Error analysis of iteration 2 (hand labels, 141 traces)

**Method.** The process is the same as the baseline analysis (REPORT.md section 3, `error_analysis.md`).

- **Data:** 47 queries × 3 runs, each run on a fresh copy of `store.db`.
- **Labels:** I read every trace in full, checked every reply against `db_facts.py`, and recorded the first failure, any secondary code, `false_claim` and a note.
- **Automated cross-check:** a scan of every reply looked for an order date placed next to "delivered", "shipped", "cancelled" or "arrived". It found no case of L beyond the labelled ones.

| Code | Failure mode | Baseline | Iteration 2 | Of which false claims |
|---|---|---:|---:|---:|
| A | Invents an ID instead of searching | 22 | 6 | 1 |
| B | Asks the user instead of looking it up | 15 | 0 | — |
| D | Invents query syntax | 10 | 0 | — |
| F | Return action not executed | 7 | 0 | — |
| C | Empty response | 7 | 0 | — |
| **L** | **Calls the order date a ship or delivery date** | 6 | **16** | 16 |
| H | Invents policy or facts | 5 | 1 | 1 |
| E | Search term misses catalog words, no retry | 4 | 5 | 3 |
| J | Misreads tool output (other than dates) | 4 | 5 | 5 |
| K | Tool rejects valid input (case-sensitive email) | 3 | 3 | 3 |
| I | Stops mid-chain | 1 | 3 | 1 |
| **Fails** | | **84** | **39** | **30** |

**What this shows**

- **The agent now nearly always fetches the data.** Only 14 failures stop the needed data from reaching the model (A, E, K), against 61 in the baseline. 22 of 39 failures (56%) happen at the last step: answering faithfully from data the agent already has.
- **Code L is now the most common failure.** It is the first failure in 16 traces and a secondary code in 1 more, so 17 in all, against 11 in the baseline.
  - **Where:** almost all are order lists from `search_orders`, which prints the order date in bare brackets: `Order #5: shipped — $299.98 (2026-03-25)`. The agent reads it as "shipped on 2026-03-25".
  - **Always-fail queries:** Q2, Q7 and Q20 (email lookups) fail all 3 runs with L.
  - **The docstring alone does not fix this.** The new `search_orders` docstring says "order date", but the output still shows a bare date.
  - **Trace IDs:** 2 runs 0–2, 7 runs 0–2, 9 run 1, 14 runs 0 and 2, 20 runs 0–2, 30 run 0, 33 runs 0 and 2, 34 run 2, and S11 run 2 (secondary).
- **False claims:** 30 of 141 traces (21%, CI 15–29%), against 41 (29%, CI 22–37%) in the baseline.
  - The overall rate is not clearly lower.
  - The share of failures that are false claims rose from 49% to 77%. Failures used to be mostly unhelpful; now they are mostly wrong.
  - **The code evals cannot see these.** The fact eval's groundedness check flagged 0 of 105 runs, as in the baseline and iteration 1.
- **ID grounding.** Of 69 ID-argument calls, the check in `labels.py` flags 6 traces. All 6 are the code-A traces (S6 runs 0–2 and S9 runs 0–2), and there are 0 false flags.

**Slices by how the user names the entity**

| Reference | Baseline | Iteration 2 | Main failure now |
|---|---|---|---|
| Product name | 4/27 (15%) | 24/27 (89%) | I: the agent never fetches the price for S8 |
| Category / browse | 4/18 (22%) | 12/18 (67%) | E: "skincare", "book cooking" |
| Email | 7/24 (29%) | 9/24 (38%) | **L (11)**: order dates in lists |
| Order ID | 38/63 (60%) | 54/63 (86%) | L (5), J (4) |
| No entity | 4/6 | **0/6** | A: invented order IDs |

### 4.1 Regressions and new risks (trace IDs)

- **"What is your return policy?" (S9) now triggers the write tool.**
  - **Run 1** called `initiate_return(order_id=1, reason="I changed my mind about the purchase.")`. This created a return on Alice Johnson's order #1, and the agent reported it to the customer.
  - **Runs 0 and 2** also called `initiate_return`, with `order_id=null` and `order_id=0`. Both calls failed.
  - **Comparison:** the baseline invented a "30-day policy" instead (H). Iteration 1 was not traced.
  - **Likely cause:** the new `initiate_return` docstring ("Start a return and refund request … Use this only when the customer asks to return") gives the word "return" a strong match, and the model has no tool for policy questions.
  - This is the most harmful failure in iteration 2, because it changes data on a third party's order.
- **"Where is my order?" (S6) fails all 3 runs (A).** The agent calls `lookup_order` with 12345, 12345 and 123456, then asks for an email or the correct ID. Nothing false is shown. The baseline asked for the order ID, with no tool call, in all 3 runs.
- **Q22, "books about cooking", fails in runs 1–2 (E).** `search_products("book cooking")` finds nothing, and the agent says "there are no books about cooking in our catalog". Run 0 searched "cookbook" and found both cookbooks. In iteration 1, the agent called `list_categories("books")` in all 3 fact-eval runs.
- **S8, "in stock and how much?", fails all 3 runs (I).** The agent answers the stock half only. Run 2 invents a price of $25.00; the real price is $69.99.
- **S5, "Do you sell laptops?": run 2 says "We also sell laptops directly" (H).** The store sells none.

### 4.2 Improvements against the baseline (trace IDs)

- **No B, C, D or F failures.** The agent always calls a tool, never invents query syntax, and always acts on a return request.
- **Returns now work.**
  - Q4 creates the return in all 3 runs, and gives the refund amount in runs 0 and 1. Run 2 says "approved" for a requested return, which is J.
  - Q23 and Q31 report the existing return in all runs.
  - S2 and S3 explain why the return is refused in all runs.
- **Product and stock questions pass every run:** inventory 18/18, product info 12/12, and shipping 15/15.

---

## 5. Pending review (BORDERLINE labels)

There are 13 BORDERLINE labels: 12 passes and 1 fail. They are in `error_analysis_data/label_data_docstrings_only.py`. The CSV `note` column drops the prefix on the fail.

| Trace | Label | Why it is a close call |
|---|---|---|
| 5 runs 0–2 | pass | The reply lists all 15 in-stock Fitness products with prices, but gives no unit counts, which the reference has. |
| 12 run 2 | fail (J) | The reply says "out for delivery since 2026-04-03"; that is the ship date. |
| 18 run 1 | pass | The reply reports the existing return correctly, but calls its reason "the reason you provided". |
| 22 run 0 | pass | The reply finds both cookbooks, and calls the Python Programming Cookbook a book about cooking. |
| S5 runs 0–1 | pass | The reply offers the Laptop Sleeve, but does not say that no laptops are sold. |
| S7 runs 0–1 | pass | The reply gives the status and total, then asks the *user* for the tracking information. |
| S10 runs 0–2 | pass | The reply does not confirm that the order is pending. |

---

## 6. What the docstrings did, and what the output format did

An exploratory version used the same docstrings **and** returned JSON instead of text. It is labelled in `error_analysis_data/better_tool_docstring_summary.md`, and its code is saved in `iterations/better_tool_docstring_src/`. Comparing three versions separates the two effects:

- **Iteration 1 → iteration 2:** the docstrings only.
- **Iteration 2 → the JSON version:** the output format only.

| Signal | Iteration 1 | Iteration 2 (docstrings) | JSON version (docstrings + JSON) | Attributed to |
|---|---|---|---|---|
| Q22 "books about cooking" (fact eval, asked-for) | 3/3 | 1/3 | 1/3 | **Docstrings** (`search_products` routing) |
| `initiate_return` tool eval | 8/8 | 8/8 | 5/8 | **JSON output** (the reply repeats the `note` and drops the refund) |
| Return scenarios | 11/14 | 14/14 | 11/14 | JSON output |
| Garbled word in the reply ("shased") | — | 0 traces | 3 traces | Probably the JSON output |
| Order-list misreads (J on email queries) | — | 1 | 7 | JSON output |
| L, order date as delivery date (first or secondary) | — | 17 | 17 | Neither: renaming the field to `order_date` did not help |
| S6 invented order IDs | not traced | 3/3 | 3/3 | Docstrings, or something unchanged since iteration 1 (not traced) |
| Hand-label pass rate | not labelled | 102/141 (72%) | 98/141 (70%) | Noise |
| Held-out scenarios pass^1 | 86% | 93% | 90% | Noise |

**Conclusions**

- **The docstrings help tool choice in most places** (returns, "ask for the email"), but they send "do you have X?" questions to `search_products`, which fails on multi-word phrases.
- **The JSON outputs made things slightly worse.** They led to more misread order lists, garbled words and dropped refund amounts. That version should not be adopted as it stands.
- **The order-date failure (L) needs an output change, not a docstring change.** It persists with text and with a field named `order_date`.

---

## 7. Limitations

- **One labeller.** I labelled every trace. The 13 BORDERLINE labels and the false-claim flags should be reviewed by the project owner.
- **No iteration 1 traces.** The hand-label comparisons are baseline → iteration 2. Code-eval comparisons are iteration 1 → iteration 2.
- **Small samples.** Every iteration 1 → iteration 2 difference is inside the confidence intervals. Section 3 lists per-query shifts as leads to investigate, not as results.
- **The docstrings were written before this measurement.** They were not tuned on these evals, so there is no selection bias in this iteration. They were also not optimized.
- **The multi-turn results do not log tool arguments.** So the privacy check in 3.4 relies on reading the replies.

---

## 8. Next steps (candidates for iteration 3)

1. **Stop write actions on questions that are not return requests (S9).**
   - Add a deterministic guard: `initiate_return` runs only when the user's message names an order ID and asks to return it.
   - Add policy and FAQ questions to the held-out set.
   - This comes first because it changes data on another customer's order.
2. **Fix L in the output, not the docstring.**
   - Print `ordered 2026-03-25` in `search_orders`, and `Order date:` in `lookup_order`.
   - Measure it with the order-date scan used in section 4, turned into a code check.
   - L is now the most common failure (17 traces), and every L is a false claim.
3. **Keep the docstrings, and fix the `search_products` routing.**
   - Either point "do you have any *kind* of X" questions to `list_categories`, or make `search_products` split multi-word queries.
   - Then re-measure Q22, Q27 and the tool eval.
4. **Ask before looking up when no entity is given (S6).**
   - Apply the same argument check as the ID-grounding evaluator: refuse `lookup_order` when the ID appears in no message.
5. **Answer both halves of two-part questions (S8).**
   - Either let `check_inventory` return the price too, or check in the eval that both facts appear in the reply.

---

## Appendix: reproducing iteration 2

On branch `optimization_3`, `src/agent/tools.py` is the iteration 2 version, also saved as `report/iterations/docstrings_only_src/tools.py`. Iteration 1 is branch `optimization_2`. The runs were made on 2026-10-10, from commit `ee1be43` (the tip of `optimization_2`) plus that file.

```bash
poetry run python -m unittest discover tests

# Evals (each run uses a fresh copy of store.db)
poetry run python -m eval.run_fact_eval --runs 3 --out report/results/fact_eval_docstrings_only.json
poetry run python -m eval.run_scenario_eval --runs 2 --out report/results/scenarios_docstrings_only.json
poetry run python -m eval.run_multiturn_eval --runs 3 --out report/results/multiturn_memory_docstrings_only.json
poetry run python -m eval.run_multiturn_eval --runs 3 --no-memory --out report/results/multiturn_no_memory_docstrings_only.json
poetry run python -m eval.run_tool_eval --runs 4 --seed 0 --out report/results/tool_eval_docstrings_only.json

# Analysis (no agent calls)
poetry run python -m eval.analyze_failures report/results/fact_eval_baseline.json report/results/fact_eval_v8.json report/results/fact_eval_docstrings_only.json
python3 -m eval.pass_k report/results/fact_eval_baseline.json report/results/fact_eval_v8.json report/results/fact_eval_docstrings_only.json
python3 -m eval.pass_k --key pass_asked report/results/fact_eval_baseline.json report/results/fact_eval_v8.json report/results/fact_eval_docstrings_only.json
python3 -m eval.pass_k --by phrasing report/results/scenarios_baseline.json report/results/scenarios_v8.json report/results/scenarios_docstrings_only.json
python3 -m eval.pass_k report/results/multiturn_memory.json report/results/multiturn_memory_docstrings_only.json report/results/multiturn_no_memory_docstrings_only.json

# Traces, labels and CSV
poetry run python report/error_analysis_data/collect_traces.py . report/error_analysis_data/traces_docstrings_only.jsonl 3
python3 report/error_analysis_data/labels.py --labels label_data_docstrings_only report/error_analysis_data/traces_docstrings_only.jsonl report/error_analysis_data/labels_docstrings_only.csv
```

- **Tool eval settings:** `--runs 4 --seed 0` reproduces iteration 1's exact questions. I checked this by replaying the question picker, with no agent calls.
- **Iteration 1's tool-eval results:** these were read from the committed `report/results/tool_eval_v8.json`. The working-tree copy has a stray edit that makes it invalid JSON, and it was left untouched.
