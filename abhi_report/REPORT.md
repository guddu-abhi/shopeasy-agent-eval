# ShopEasy Support Agent: Evaluation and Improvement Report

## Summary

This report defines what good performance means for the ShopEasy support agent, measures the original agent against that definition, and improves it in two iterations. The model (`qwen2.5:3b`) and the LangGraph agent design stay the same throughout.

| Metric | Baseline | Iteration 1 (prompt + tools + memory) | Iteration 2 (+ docstrings) |
|---|---|---|---|
| 43 held-out scenarios, never used for tuning (pass^1) | 70% | 86% | **93%** |
| 35 original questions, right in all 3 runs, strict scorer (pass^3) | 23% | **80%** | 71% |
| 35 original questions, right in all 3 runs, asked-for scorer (pass^3) | 34% | **91%** | 80% |
| Multi-turn sessions with memory (runs passed) | — | 17/18 | **18/18** |
| Hand-labeled traces that pass (141) | 40% | 65% | **72%** |

The strict scorer also requires details the customer did not ask for. The asked-for scorer checks only what the question asks. Section 3 explains both.

- **Approach.** I first defined "good" as correct answers taken from the data, with no harm to customers. I then read 141 baseline traces to find out how the agent fails, built evals that check each failure, and made one change at a time.
- **The main finding.** 73% of the baseline's failures happened before the model saw any data: it invented IDs, asked the customer instead of looking things up, or used search syntax that found nothing. The 3B model also does not chain tool calls, even though LangGraph gives it every tool result.
- **What fixed it.** A prompt that shows the exact call for each tool, and tools that accept what customers actually say, such as a product name, so that one call is enough. Five of the original failure modes dropped to zero. In iteration 2, clearer docstrings improved return handling and stopped a privacy leak.
- **What is not ready.** Iteration 2 is the best version, but it should not be released yet. A policy question can create a return on another customer's order, and the agent still mislabels order dates. Section 6 sets out the next steps.

## 1. What performance means at this stage

### Where the project stands

The ShopEasy agent is a prototype. A small local model (`qwen2.5:3b`) answers customer questions by calling tools that read a store database, and one tool, `initiate_return`, can write to it. Before this work, nobody had defined what a good answer was. The eval script printed the replies but did not score them.

At this stage, performance should answer two plain questions:

1. **Does the agent give the customer a correct answer, taken from the data?**
2. **Does it avoid doing harm?** Harm means stating something false, acting on the wrong order or product, or showing one customer's data to another.

Tone, speed and cost are left for later. They will matter once the agent serves real customers, but there is little point in polishing them while the baseline still gets more than half of its answers wrong (it passes 41% of its runs on the original questions).

### What "good" looks like

The table below defines good performance for this agent. It sorts everything the agent can get right or wrong into three groups, and each group has its own rule:

- **Release blockers must never happen.** The target is zero failures, because a single failure can hurt a customer. They are also counted on their own, so a good pass rate cannot hide them.
- **The core metric is what we try to improve.** A new version is better only if it scores higher than the previous one and the gap is larger than the run-to-run noise.
- **Tolerable flaws are known problems that we accept for now.** They do not count against the agent, so they do not distract from the two groups above.

| Group | The agent should… | Why it matters | How it is measured |
|---|---|---|---|
| **Release blocker** (target: 0) | Never state a fact the tools did not return, such as an invented price, stock count or ranking. | The customer has no reason to doubt a confident answer. | A code check that every number in the reply came from a tool. It is only partial, because it misses false statements without numbers, such as "no orders found". |
| | Never answer about a product, order or customer that the customer did not name. | The reply looks correct but describes a different item, or shows another customer's orders. When a customer asked for "my orders" without giving an email, iteration 1 searched the prompt's example email and listed the orders of Grace Kim, a customer in the database, in 2 of 12 saved runs. | Key-fact check, plus manual review. A check that every email and ID in a tool call came from the customer is still to be built. |
| | Hold a conversation reliably: answer follow-ups from the earlier turns of the same session, and never carry anything from one session into another. | Customers often give details over several turns. Without memory, the agent answered "who is shipping it?" about an order the customer never mentioned. A working conversation also shows early that the LangGraph design can support real customers, which a prototype should prove. | 6 two-turn sessions × 3 runs (`eval/run_multiturn_eval.py`). Each session checks the facts in the final reply, that no data from another session appears, that every number came from a tool, and the database state. |
| | Create a return only when allowed, and never twice. | This is the only action that changes the database. | Database state check after each run. |
| | Never send an empty reply. | The customer gets no help at all. | Non-empty check. |
| **Core metric** (higher is better) | Give the customer what they asked for. | This is the agent's job. | One pass or fail per question, reported as pass^k on the original questions and on held-out questions that were never used for tuning. |
| **Tolerable for now** | Missing details nobody asked for, imperfect wording, and shortened product names are accepted. | These are annoying but not harmful, and fixing them now would pull effort away from correctness. | The asked-for scorer ignores them. The strict scorer counts missing details, so the report gives both scores (Section 3). |

### Why each question gets a single pass or fail

The first metric counted the key facts found across all replies (for example, 114 of 156 facts). It had two problems:

- **Questions were weighted unevenly.** One question had 11 facts and another had 1, so two inventory questions dominated the total.
- **Wrong answers got partial credit.** A reply could contain some correct facts and still mislead the customer.

Each run now passes only if **every** check passes. The key facts must be in the reply, every number must come from a tool, and the reply must not be empty. This is easier to read ("30 of 35 questions answered correctly"). It is also easier to label by hand, which matters because the scorer itself was checked against hand labels.

### Why pass^k is the headline number

The agent is not deterministic. In the baseline, 17 of 47 questions got different results across 3 runs of the same input. A customer gets one answer and has no reason to ask again, so the agent must be right **every time**, not just sometimes.

- **pass^k ("pass all k")** runs each question k times and counts it only if **all** k runs pass. pass^3 is the share of questions answered correctly in all 3 runs, so it measures reliability. It comes from the τ-bench paper, and it falls as k grows when an agent is flaky.
- **pass@k ("pass at least once")** counts a question if **at least one** of its k runs passes. It shows whether the agent *can* answer, not whether it does so every time. I report it only to show flakiness.
- **Example.** A question that passes in 2 of 3 runs counts for pass@3 but not for pass^3. On the baseline, pass@3 is 57% but pass^3 is only 23%. So the baseline could answer more than half the questions at least once, but it answered fewer than a quarter of them reliably.
- Both are computed from saved runs by `eval/pass_k.py`, with no new agent calls.

The same metrics apply to the reworded questions ([`iteration_1_reworded_questions.json`](results/iteration_1_reworded_questions.json), [`iteration_2_reworded_questions.json`](results/iteration_2_reworded_questions.json)). There are 16 questions, 2 for each of the 8 tools, and each runs 4 times with a different wording picked at random. A run passes only if the reply has every expected fact. The baseline was not run on this set.

| Reworded questions | Baseline | Iteration 1 | Iteration 2 |
|---|---|---|---|
| pass^1: single runs that pass | not run | 95% (61/64 runs) | 94% (60/64 runs) |
| pass^4: questions that pass in all 4 wordings | not run | 81% (13/16) | 75% (12/16) |
| pass@4: questions that pass in at least one wording | not run | 100% (16/16) | 100% (16/16) |

Both iterations answer every question correctly at least once. The drop from pass^1 to pass^4 shows which wordings still trip the agent.

## 2. Baseline error analysis

Before changing anything, I studied how the baseline agent fails. I followed the error-analysis process from Hamel Husain and Shreya Shankar's [LLM Evals FAQ](https://hamel.dev/blog/posts/evals-faq/).

- **Traces.** I ran the `main` agent on the 35 original questions plus 12 edge cases. I wrote the edge cases from the database before any run. Each question ran 3 times, which gives **141 traces**. Each trace records every message, tool call and tool result ([`baseline_traces.jsonl`](results/baseline_traces.jsonl)), and each one used a fresh copy of the database.
- **Labels.** An AI assistant and I read every trace together. For each trace, we recorded pass or fail, the first thing that went wrong, and whether the reply told the customer something false. I then reviewed the labels in [`baseline_labels.csv`](results/baseline_labels.csv) by hand.
- **Grouping.** We grouped the first failures into failure modes and counted them. Each mode has a letter code that the rest of the report uses. Each code also has a short slug in parentheses, such as A (`invented_id`), so it can be read at a glance. All 13 codes are listed in the [failure codes](#failure-codes) table in the appendix.

**Result: the baseline passes 57 of 141 traces (40%), so 84 traces fail.**

### What this shows

- **Most failures happen before the model sees any data.** In 61 of the 84 failures (73%), the first failure was one of the six modes below. In each of them, the data the agent needed never reached the model.

  | Code | What happened | Fails | Example (question → what the agent did → the truth), from [`baseline_traces.jsonl`](results/baseline_traces.jsonl) |
  |---|---|---:|---|
  | A (`invented_id`) | It called a tool with an invented ID, so it got the wrong product or nothing. | 22 | "Is the Blue Ultraboost Running Shoe currently in stock?" → `check_inventory(product_id=12345)` → "I couldn't find information about a product with the ID 12345." (line 1). The shoe is product #1, with 45 in stock. |
  | B (`asked_customer_instead`) | It asked the customer instead of calling a tool. | 15 | "How much does the Leather Messenger Bag cost?" → no tool call → "Could you provide the product ID, please?" (line 10). It costs $189.99. |
  | D (`invented_search_syntax`) | It called a search tool with invented syntax, so the search found nothing. | 10 | "Show me all of bianca@example.com's orders." → `search_orders("email:bianca@example.com")` → "It seems there are no orders found for the email address bianca@example.com." (line 20). Bianca has 3 orders. |
  | C (`empty_reply`) | It sent an empty reply and made no tool call. | 7 | "What is the status of order #7?" → no tool call → empty reply (line 9). The order shipped with FedEx. |
  | E (`unknown_catalog_word`) | It searched with a word that is not in the catalog. | 4 | "What skincare products do you have?" → `search_products("skincare")` → "it seems there are no skincare products currently listed in our database." (line 74). The store has 14 in the Beauty category. |
  | K (`tool_rejects_input`) | It searched with an email in different capital letters, and the exact-match search found nothing. | 3 | "Show me orders for Alice@Example.com" → `search_orders("Alice@Example.com")` → "I couldn't find any orders for the email address Alice@Example.com." (line 47). Alice has 4 orders under `alice@example.com`. |
  | | **Total** | **61** | |

- **The other 23 failures happened after the agent had the data it needed.** It misread the data, invented facts, or did not finish the task.

  | Code | What happened | Fails | Example (question → what the agent did → the truth), from [`baseline_traces.jsonl`](results/baseline_traces.jsonl) |
  |---|---|---:|---|
  | F (`return_not_created`) | It looked up the order but never created the return. | 7 | "I want to return order #14, the bluetooth speaker stopped working after a week." → only `lookup_order(14)` → "Could you please provide your contact information so we can proceed with the return?" (line 98). No return was created. |
  | L (`order_date_mislabeled`) | It called the order date a delivery date. | 6 | "How much was order #17?" → `lookup_order(17)` → "The order was delivered on 2026-01-30." (line 62). That is the date the order was placed. |
  | H (`invented_policy_fact`) | It invented a policy or a fact. | 5 | "What is your return policy?" → no tool call → "Our return policy allows you to return items within 30 days of receiving them." (line 44). The store has no policy data. |
  | J (`misread_tool_output`) | It misread the tool output. | 4 | "Has order #25 been delivered yet?" → `get_shipping_status(25)` → "It is currently in transit…" (line 59). The tool said `out_for_delivery`. |
  | I (`stopped_mid_chain`) | It found the product, then stopped before the second call. | 1 | "Is the Robot Vacuum Cleaner currently in stock? How many do you have?" → `search_products` finds #46 → "However, I don't have current inventory information available." (line 21). There are 20 in stock, and `check_inventory` was never called. |
  | | **Total** | **23** | |

  So most fixes belong in the tools and in how they are called, not in the wording of the answers.
- **About half the failures tell the customer something false.** While labeling, we flagged each failing trace that states something untrue or unsupported by the data. 41 of the 84 failing traces carry this flag. By failure mode, the count is: D 9, L 6, A 5, H 5, F 5, E 4, J 4 and K 3. The other 43 failures are unhelpful but say nothing false, such as asking for an ID or sending an empty reply. How often a failure happens and how much harm it does are different things:
  - Invented search syntax (D) and mislabeled dates (L) are in the middle by frequency, but almost every one is a false statement: 9 of 10, and 6 of 6.
  - Invented IDs (A) are the most common failure. However, only 5 of the 22 state something false. Most lead to "I couldn't find ID 12345", which is unhelpful but true.
- **How the customer names the item predicts failure.** It predicts failure better than the type of question does:

  | How the customer names it | Pass rate |
  |---|---|
  | Product name | 4/27 (15%) |
  | Category | 4/18 (22%) |
  | Email | 7/24 (29%) |
  | Order ID | 38/63 (60%) |

  The baseline works mainly when it is handed an ID. Customers usually give a name or an email.
- **The agent is flaky.** 17 of 47 questions got different results across 3 runs of the same input, and 20 failed every time. A single run per question cannot compare two versions, so every later result uses repeated runs and pass^k.

### Problems found in the eval set itself

- **Some expected facts were impossible to reach.** Some expected answers needed data that the original tools never returned: the refund of an existing return (Q18, Q31), its reason (Q18, Q23, Q31), and stock counts from a product search (Q5). No agent could pass these questions with the original tools.
- **Some reference answers were wrong or incomplete.**
  - Q16 lists one pair of sunglasses, but the store sells two.
  - Q18 says the boots came in the "wrong color", but the existing return says the "sole separated after one hike".
  - Q13 is labeled `order_status`, but it asks for order details.
- **The original eval was not fit to measure improvement.** It printed replies without scoring them, logged no tool calls, and ran each question once. It also wrote to the real database: in 1 of 3 runs, Q4 created a real return, which changed the correct answer for every later run.

These counts describe this test set, not real customer traffic. The questions are curated and partly synthetic, so a mode's share here does not predict how often real customers would hit it.

## 3. How it is measured

Most checks from the criteria table (Section 1) run as code. False statements and privacy leaks also need a manual review. Every result comes from repeated runs on a fresh copy of the database.

| Eval | What it answers | Example | Size |
|---|---|---|---|
| `eval/run_fact_eval.py` | Does the agent answer the 35 original questions? | "Is the Robot Vacuum Cleaner currently in stock? How many do you have?" The reply must say it is in stock with 20 units, and every number must come from a tool. | 35 questions × 3 runs |
| `eval/run_tool_eval.py` | Does it give the same answer when the same question is worded differently? | "What categories are available in your store?", "What kinds of things can I buy here?" and three other wordings. Each reply must list all 10 categories. | 16 questions × 4 wordings |
| `eval/run_scenario_eval.py` | Does it work on new cases that were never used for tuning? | "I would like to return order #29 because it doesn't fit." Order #29 is still pending, so the reply must refuse, and the database must have no new return afterwards. | 43 scenarios × 2 runs |
| `eval/run_multiturn_eval.py` | Does it keep context within a conversation, and only within it? | Turn 1: "Can you show me all my orders?" Turn 2: "Sure, it's karen@example.com". The second reply must list Karen's three orders ($379.98, $154.96 and $57.98). | 6 sessions × 3 runs |
| `tests/test_tools.py` | Do the tools return the right data? | `test_pending_order_cannot_be_returned`: a return on a pending order is refused, and no row is written. | 13 unit tests, no LLM |
| `.github/workflows/eval.yml` | Did a change break something? | A pull request runs 8 original questions (such as Q2, "Show me all orders for alice@example.com") twice each. | Unit tests on every push, plus the 8-question smoke test, which fails below a 60% pass rate |

- **There are two scorers, and both were checked against hand labels.** The strict scorer requires every key fact in the reference answer, including details nobody asked for, such as a tracking number for "Which carrier is it?". The asked-for scorer checks only what the question asks. 40 sampled runs were labeled by hand in the same way as the baseline traces ([`scorer_audit.csv`](results/scorer_audit.csv)). The asked-for scorer agreed with these labels 82% of the time, and the strict scorer 72% of the time. The headline numbers use the strict scorer because it is the harder test, and the results tables also show the asked-for score.
- **The code check misses most false statements.** It checks that every number in a reply came from a tool. It flagged none of the 105 baseline runs on the original questions, while the hand labels found 41 false claims in the 141 baseline traces. Most false claims contain no number, such as "no orders found" or an invented "30-day return policy".

## 4. Iteration 1: prompt and tool changes

Every change started from a failure in the error analysis. I made one change at a time, measured it, and kept it only if it helped. While tuning, I used quick checks (asking one question 5–6 times) and the older score that counted correct facts. The final before-and-after comparison uses the pass/fail evals. The full tuning log, with every intermediate prompt, is kept in the git history: run `git show iteration-2:report/prompt_tuning.md`. The probe numbers in this section (such as 2 of 60 and 48 of 48) come from that log. The probes were not saved as result files, unlike the eval runs in `results/`.

### The prompt: show the model which tool to call

The original prompt was five general lines. It never named a tool or showed how to use one. The new prompt has four short rules and a "Which tool to call" section. For each tool, it shows an example question and the exact call it needs:

```
### All orders for a customer -> search_orders
Search with the customer's exact email address. If they did not give one, ask for it.
- "List every order for grace@example.com." -> search_orders(query="grace@example.com")
```

<details>
<summary><b>The full prompts, before and after</b></summary>

The baseline prompt (`src/agent/prompts.py` on `main`):

```
You are a customer support assistant for ShopEasy, an online retail store.
Help customers with their questions about orders, products, shipping, and returns.
Be friendly, concise, and helpful.
Use the available tools to look up information before answering.
If you cannot find the information the customer needs, let them know and suggest next steps.
```

The iteration 1 prompt (`src/agent/prompts.py` at the tag `iteration-1`), exactly as the model receives it. Iteration 2 uses the same prompt. In the source code, rule 1 has a `{TOOL_NAMES}` placeholder that is filled in with the 8 tool names.

```
You are ShopEasy's customer support assistant. Help customers with orders, products, shipping, and returns. Be friendly and concise.

## Rules
1. Call only these tools, using their exact names: lookup_order, search_orders, get_product_details, search_products, list_categories, check_inventory, get_shipping_status, initiate_return.
2. Get facts only by calling a tool. Never answer from memory, because store data changes.
3. Answer using only what the tool returns. If it has nothing useful, say so and suggest a next step.
4. Never guess an ID. If the customer names a product, pass the product name instead.

## Which tool to call
Each entry lists example customer questions and the tool calls they need. The examples teach you to recognize the intent; customers may phrase it differently.

### What the store sells -> list_categories
- "What categories are available in your store?" -> list_categories(category="all")
- "What type of products do you sell?" -> list_categories(category="all")
When the customer asks which products of a kind you have, pass that kind as the category:
- "Which toys do you sell?" -> list_categories(category="toys")
- "I need new clothes. What clothing do you carry?" -> list_categories(category="clothing")
- "What gadgets do you have?" -> list_categories(category="Electronics")
After listing categories, offer to show the products in one.

### Finding a product by name -> search_products
Search with one short keyword from the product name, in singular form.
- "Do you sell headphones?" -> search_products(query="headphone")
- "Do you carry a French press?" -> search_products(query="french press")

### Product price or details -> get_product_details
- "What does the Ceramic Coffee Mug cost?" -> get_product_details(product="Ceramic Coffee Mug")
- "Describe product #20." -> get_product_details(product="20")

### Stock levels -> check_inventory
- "Is the Trail Hiking Boot in stock?" -> check_inventory(product="Trail Hiking Boot")
- "How many of product #12 are left?" -> check_inventory(product="12")

### One order's date, items, or total -> lookup_order
- "What did I buy in order #31?" -> lookup_order(order_id=31)
- "What was the total of order #50?" -> lookup_order(order_id=50)

### Order status -> lookup_order and get_shipping_status
- "What's happening with order #53?" -> lookup_order(order_id=53), then get_shipping_status(order_id=53)

### Shipping, tracking, or delivery -> get_shipping_status
- "Who is delivering order #22, and when?" -> get_shipping_status(order_id=22)
- "Can I get the tracking code for order #44?" -> get_shipping_status(order_id=44)

### All orders for a customer -> search_orders
Search with the customer's exact email address. If they did not give one, ask for it.
- "List every order for grace@example.com." -> search_orders(query="grace@example.com")

### Returns -> initiate_return
- "I'd like to send back order #38, the pants don't fit." -> initiate_return(order_id=38, reason="pants don't fit")
If the tool says a return already exists or the order cannot be returned, tell the customer exactly that.
```

Source: [`prompts_and_tool_schemas.json`](results/prompts_and_tool_schemas.json).
</details>

The rules tell the model to use only the listed tools by their exact names, to take facts only from tools, and never to guess an ID.

The new prompt fixed four failure modes: asking the customer instead of looking it up (B), empty replies (C), invented search syntax (D), and returns that were never created (F). For example, once the prompt showed a plain email, the agent stopped writing `email:bianca@…`, and email lookups went from 20 of 32 correct facts to 32 of 32.

Three things I learned about prompting this small model:

- **Long examples backfired.** When an example included a sample reply, the model copied that reply word for word, or it made up tool names such as `get_order_status`, which came back as empty replies. Short "question → tool call" lines, with no sample reply, avoided both problems.
- **Explaining multi-step plans did not help.** A version that told the model to "search first, then look up" scored no better and doubled the empty replies, so I dropped it.
- **Fixing one question can break another.** A change aimed at catalog questions caused empty replies on "Where is my order #2?". After that, I checked every change on all question types.

### The tools: one call should be enough

The most important finding of this iteration is that **this model does not chain tools**. "Chaining" means using the result of one tool call as the input to the next. With the original tools, a question like "Is the Kettlebell in stock?" needs two calls: `search_products` finds the product ID, and then `check_inventory` uses it. Across five prompt versions, including one with step-by-step worked examples, the model did this in only **2 of 60 runs**. Instead, it invented an ID, took the "25" from "Kettlebell 25lb" as the ID, or stopped after the search.

**The model has the information, but it misses the planning step.** LangGraph's agent loop (`create_react_agent`) passes every tool result back to the model and lets it call another tool. The run ends only when the model replies without asking for a tool. So the 3B model is not short of context; it decides not to make the second call. This baseline trace shows it clearly (question 21, run 0, [`baseline_traces.jsonl` line 21](results/baseline_traces.jsonl#L21)):

| Step | What happened |
|---|---|
| 1. Customer | "Is the Robot Vacuum Cleaner currently in stock? How many do you have?" |
| 2. Model | Calls `search_products("Robot Vacuum Cleaner")`. |
| 3. Tool | Returns "#46: Robot Vacuum Cleaner (Electronics) — $349.99". |
| 4. Model | "It's product ID #46 … To check if it's in stock, we would need to use the `check_inventory` tool with the product ID #46. Could you please proceed with using the `check_inventory` tool…?" |

At step 4, the model had the right ID and even named the right tool. However, it asked the customer to run the tool instead of calling it itself, and the run ended. The correct answer was 20 in stock. A larger model would probably chain these calls, but I could not test one, because the challenge fixes the model.

So instead of rewording the prompt again, I changed the tools so that each answer needs only one call.

### What changed in each tool

The model never sees a tool's code. For each tool, `bind_tools` sends it three things: a name, a description taken from the docstring, and the names and types of the arguments. Iteration 1 changed 4 of the 8 tools. The other 4 are exactly the same as on `main`. To see the code change, run `git diff baseline iteration-1 -- src/agent/tools.py`.

| Tool | Arguments | Docstring | What the code returns | Fixes |
|---|---|---|---|---|
| `lookup_order` | Same | Same | Same | — |
| `search_orders` | Same | Same | Same | — |
| `get_product_details` | `product_id: integer` → `product: string` (an ID or a name) | Rewritten | Finds the product by ID, exact name or whole words. A close match is labeled "No exact match". | A, I |
| `check_inventory` | `product_id: integer` → `product: string` (an ID or a name) | Rewritten | The same name matching as `get_product_details`. | A, I |
| `search_products` | Same | Same | Same | — |
| `list_categories` | New tool: `category: string`, required | New | Lists the in-stock products of a kind, or every category with counts and price ranges. It never returns nothing. | B, E |
| `get_shipping_status` | Same | Same | Same | — |
| `initiate_return` | Same | Same | For an existing return, it also gives the reason and refund amount, and says that no new return was created. | Facts no tool returned |

Each changed tool is described below, with the same question answered in both stages. The trace line numbers are the same in both files, because both were collected in the same order.

**`get_product_details` and `check_inventory`: accept a product name**

| | Baseline (`main`) | Iteration 1 (`iteration-1`) |
|---|---|---|
| Name and arguments | `get_product_details(product_id: integer)`<br>`check_inventory(product_id: integer)` | `get_product_details(product: string)`<br>`check_inventory(product: string)` |
| `get_product_details` docstring | "Get information about an item. Returns details for the requested item." | "Get a product's name, category, price, and description. Pass the product's ID (e.g. "33") or its name (e.g. "Vacuum Insulated Tumbler")." |
| `check_inventory` docstring | "Check product availability. Use this to see if a product is available." | "Check whether a product is in stock and how many units are available. Pass the product's ID (e.g. "159") or its name (e.g. "Kettlebell 25lb Cast Iron")." |

- **Code:** a new helper, `_find_products`, tries the ID first, then the exact name, then whole-word matches. If only a similar product exists, the output starts with "No exact match … (not the same item)". For "Kettlebell 50lb", which the store does not sell, it offers the 25lb kettlebell under that label. Whole words matter: before this rule, "Nike Air Max" matched "Hair Clip Set". Unit tests cover both cases.
- **Why:** customers name products and do not know the IDs. With an integer ID, the model had to call `search_products` first and pass the ID on, which it did in only 2 of 60 runs. Otherwise it invented an ID such as 12345 (A) or stopped after the search (I).
- **Result:** questions that name a product passed 48 of 48 probe runs, by name or by ID.
- **Traces:** "Tell me about the Yoga Mat Premium" (question 11, run 0, line 11). The baseline called `get_product_details(product_id=12345)` and got "No product found with ID 12345." Iteration 1 called `get_product_details(product="Yoga Mat Premium")` and got the price and description. "How many Portable Phone Chargers do you have left in stock?" (question 8, run 2, line 102). The baseline called `check_inventory(product_id=123)`, which is the Insulated Cooler Bag, and told the customer there were 80 chargers. Iteration 1 called `check_inventory(product="Portable Phone Charger")` and gave the right count, 200. Sources: [`baseline_traces.jsonl`](results/baseline_traces.jsonl#L11) and [`iteration_1_traces.jsonl`](results/iteration_1_traces.jsonl#L11).

**`list_categories`: a new tool for "What do you sell?"**

| | Baseline (`main`) | Iteration 1 (`iteration-1`) |
|---|---|---|
| Name and arguments | No such tool. The closest was `search_products(query: string)`. | `list_categories(category: string)`, required |
| Docstring | — | "List the store's catalog. Pass a category or kind of product (e.g. "Footwear", "books", "toys", "yoga") to get the matching in-stock products. Pass "all" to get every category with product counts and price ranges. Use this when the customer asks what the store sells, what categories exist, or which products of a kind are available." |

- **Code:** it matches everyday words to a category ("books" finds Books, "toys" finds Toys & Games) and returns the in-stock products with IDs and prices. If no category matches, it returns the products whose names match ("yoga gear" finds the Yoga Mat). With "all", or when nothing matches, it lists all 10 categories with their product counts and price ranges.
- **Why:** no baseline tool could answer "What do you sell?". `search_products` matches only text in a name or category, so everyday words fail: `search_products("yoga gear")` returns "No products found". In the baseline traces, the agent often asked the customer to narrow the question instead of looking it up (B).
- **Result:** questions such as "Which books do you have?" passed 12 of 12 probe runs. While the argument was optional, the model often left it out: these questions passed 0 of 12, and 6 of 12 after the prompt showed the argument being passed. So the argument is required.
- **Traces:** "What outdoor gear do you sell? I'm going camping." (question 24, run 0, line 24). The baseline called no tool and asked the customer to specify. Iteration 1 called `list_categories(category="Outdoor Gear")` and listed the outdoor products with prices.

**`initiate_return`: report the existing return**

| | Baseline (`main`) | Iteration 1 (`iteration-1`) |
|---|---|---|
| Name, arguments and docstring | `initiate_return(order_id: integer, reason: string)`, "Handle a customer issue with an order. Use this when a customer has a problem." | Same. Iteration 2 rewrote the docstring (§5). |
| Output for an existing return | "A return request already exists for order #46 (Return #7, status: approved)." | "A return request already exists for order #46. No new return was created." followed by the return ID, reason, status and refund amount. |

- **Why:** the reason and the refund amount of an existing return were facts that no tool returned. So the agent could not answer questions about them, and it sometimes made up the state of the return.
- **Result:** the four return questions in the original set (Q4, Q18, Q23 and Q31, 12 runs) went from 1 of 12 in the baseline to 12 of 12 in iteration 1, with both scorers ([`baseline_original_questions.json`](results/baseline_original_questions.json), [`iteration_1_original_questions.json`](results/iteration_1_original_questions.json)). The prompt changed at the same time, so not all of this gain comes from this tool change. However, Q18, Q23 and Q31 ask about a return that already exists, and they could not pass before, because no tool returned the reason or the refund.
- **Traces:** "I want to return order #46, the pull-up bar doesn't fit my door frame." (question 31, run 1, line 78). The baseline output had no refund amount, and the reply called the approved return "already complete". Iteration 1 replied: "The return #7 has been approved. The refund amount is $34.99."

All definitions above come from [`prompts_and_tool_schemas.json`](results/prompts_and_tool_schemas.json), which holds what `bind_tools` sends to the model in each stage.

Two lessons:

- **How a tool is defined matters as much as the prompt.** When the `category` argument was optional, the model left it out (0 of 12 correct, and 6 of 12 even after the prompt showed the argument). Making it required fixed this (12 of 12). Adding a prompt rule that said "always pass a category" made it worse.
- **Every fix can create a new risk.** Once the tools accepted product names, a question about a product the store does not sell returned a similar product, and the agent presented it as the right one. The "No exact match" label fixed this.

### Session memory

The original agent treated every message as a new conversation, so a follow-up such as "How much does it cost?" lost track of the product. The agent now uses LangGraph's `MemorySaver`, which keeps the messages of each conversation under its own ID. Memory is optional, so the single-question evals are unaffected. Conversations that depend on an earlier message went from 1 of 9 correct runs to 9 of 9.

The whole conversation, including earlier tool calls and results, is sent to the model on every turn, and nothing trims it. So a very long chat could exceed the model's context window. This does not matter for short support conversations, but the history would need trimming or summarizing before production.

### Did each change fix its failure?

The table counts the failures that code can detect, on the 35 original questions run 3 times each, with the asked-for scorer.

| Failure mode | Baseline | After iteration 1 |
|---|---:|---:|
| Invented ID (A, `invented_id`) | 15 | 0 |
| Asked instead of looking up (B, `asked_customer_instead`) | 14 | 0 |
| Invented search syntax (D, `invented_search_syntax`) | 11 | 0 |
| Return never created (F, `return_not_created`) | 6 | 0 |
| Empty reply (C, `empty_reply`) | 3 | 0 |
| Needed data not found (E, `unknown_catalog_word`; I, `stopped_mid_chain`; K, `tool_rejects_input`) | 7 | 6 |
| Tool found the fact, but the reply left it out | 1 | 1 |
| **Failed runs** | **57 of 105** | **7 of 105** |

Five failure modes dropped to zero. The six "needed data not found" failures come from two questions, 3 runs each. Q5 asks which fitness products are in stock, but `list_categories` returns no stock counts, and in 2 of the 3 runs the model also passed "Electronics" as the category. Q27 asks for skincare products, and the tool does not link "skincare" to the Beauty category. With the strict scorer, failed runs fell from 62 to 16, because it also fails runs that leave out details nobody asked for.

## 5. Iteration 2: tool docstring changes

### Why docstrings

The model never sees the code inside a tool. `create_react_agent` passes each tool to the model with `bind_tools`, which sends only the tool's name, its docstring (the short description at the top of the function) and its argument types. The model uses this text to decide which tool to call and what to pass to it. Some of the original docstrings gave it almost nothing to go on. For example, `initiate_return` said only "Handle a customer issue with an order. Use this when a customer has a problem."

In iteration 2, every docstring says **when to use the tool and what it returns**, and every argument has a short description. To see the full change, run `git diff iteration-1 iteration-2 -- src/agent/tools.py`.

### Every docstring in all three stages

"Same" means that the docstring is identical to the one in the previous stage.

| Tool | Baseline (`main`) | Iteration 1 (`iteration-1`) | Iteration 2 (`iteration-2`) |
|---|---|---|---|
| `lookup_order` | "Find order information and status details. Use this to get data about an order." | Same | "Get one order's status, order date, total, customer, and items bought. Use this when the customer gives an order number and asks what they bought, what it cost, or its status. For tracking or delivery dates, use get_shipping_status." |
| `search_orders` | "Find orders matching the query. Returns a list of orders." | Same | "List every order for a customer's email address, newest first, with each order's status, order date, and total. If the customer has not given an email, ask for it instead of calling this tool." |
| `get_product_details` | "Get information about an item. Returns details for the requested item." | "Get a product's name, category, price, and description. Pass the product's ID (e.g. "33") or its name (e.g. "Vacuum Insulated Tumbler")." | "Get a product's ID, name, category, price, and description. If the result starts with "No exact match", the products are only close matches, not the item asked for." |
| `check_inventory` | "Check product availability. Use this to see if a product is available." | "Check whether a product is in stock and how many units are available. Pass the product's ID (e.g. "159") or its name (e.g. "Kettlebell 25lb Cast Iron")." | "Check whether a product is in stock and how many units are available. If the result starts with "No exact match", the products are only close matches, not the item asked for." |
| `search_products` | "Look up products in the system. Use this to find product data." | Same | "Find products whose name or category contains the keyword, with each product's ID, name, category, and price. Use this when the customer asks whether the store sells something." |
| `list_categories` | No such tool | New: "List the store's catalog. Pass a category or kind of product (e.g. "Footwear", "books", "toys", "yoga") to get the matching in-stock products. Pass "all" to get every category with product counts and price ranges. Use this when the customer asks what the store sells, what categories exist, or which products of a kind are available." | "List the store's catalog. Pass a category or kind of product to get the matching in-stock products. Pass "all" to get every category with its product count and price range. Use this when the customer asks what the store sells, what categories exist, or which products of a kind are available." |
| `get_shipping_status` | "Get order status and delivery information. Use this for order updates." | Same | "Get an order's shipment: carrier, tracking number, shipping status, ship date, and estimated delivery. Use this when the customer asks where an order is, who delivers it, when it arrives, or for a tracking number." |
| `initiate_return` | "Handle a customer issue with an order. Use this when a customer has a problem." | Same | "Start a return and refund request for a shipped or delivered order. Use this only when the customer asks to return or send back an order. Returns the return's ID, status, and refund amount. If a return already exists, no new one is created and the existing one is returned. If the order cannot be returned, the result says why." |

The baseline and iteration 1 have no argument descriptions. Iteration 2 added one to every argument:

| Argument | Tools | Description in iteration 2 |
|---|---|---|
| `order_id: integer` | `lookup_order`, `get_shipping_status`, `initiate_return` | "The order number, e.g. 14 for order #14." |
| `query: string` | `search_orders` | "The customer's exact email address." |
| `query: string` | `search_products` | "One short keyword from the product name, in singular form, e.g. "headphone"." |
| `product: string` | `get_product_details`, `check_inventory` | "The product ID (e.g. "33") or name (e.g. "Vacuum Insulated Tumbler")." |
| `category: string` | `list_categories` | "A category or kind of product (e.g. "Footwear", "toys", "yoga"), or "all"." |
| `reason: string` | `initiate_return` | "Why the customer is returning the order, in their words." |

The argument names and types are the same in iteration 1 and iteration 2. The effect of each change is measured below: `initiate_return` and `search_orders` improved, and `search_products` got worse on one question. No separate effect was measured for the other five tools. Source: [`prompts_and_tool_schemas.json`](results/prompts_and_tool_schemas.json).

### Only one thing changed

The tool code, the tool outputs, the prompt, the model and the evals are all the same as in iteration 1. The diff changes only the docstrings and the argument descriptions, not the code that builds each output, and the same 13 unit tests pass. I ran the same eval scripts with the same settings as in iteration 1. So any change in behavior comes from the new text the model reads. The docstrings were also written before any measurement, so they were not tuned to fit these evals.

### Overall results

| Metric | Baseline | Iteration 1 | Iteration 2 |
|---|---|---|---|
| 35 original questions, strict scorer, pass^1 / pass^3 | 41% / 23% | 85% / 80% | 79% / 71% |
| 35 original questions, asked-for scorer, pass^1 / pass^3 | 46% / 34% | 93% / 91% | 89% / 80% |
| **43 held-out scenarios, pass^1 / pass^2** | 70% / 63% | 86% / 79% | **93% / 91%** |
| 16 reworded questions, runs passed / questions right in all 4 wordings | — | **61/64 / 13/16** | 60/64 / 12/16 |
| Multi-turn sessions with memory (runs passed) | — | 17/18 | **18/18** |
| Hand labels: traces that pass (141) | 57 (40%) | 92 (65%) | **102 (72%)** |
| Hand labels: traces with a false claim (141) | 41 (29%) | 41 (29%) | **30 (21%)** |

- **Iteration 2 does better on the fairest test.** The held-out scenarios were never used for tuning. They rose from 86% to 93%, and the results became more consistent from run to run.
- **It does slightly worse on the 35 original questions.** This is flakiness, not lost ability. Iteration 1 and iteration 2 each answered the same 31 questions correctly at least once in 3 runs (pass@3 of 89% in both), but iteration 2 failed some of them more often.
- **Rewording a question rarely changes the answer.** A reworded run passes when the reply contains every expected fact. Both iterations passed every wording for order, inventory, product-detail and return questions. All the failures were catalog questions or one tracking question. Both iterations missed the yoga question once, in different wordings ("Do you sell anything for yoga?" in iteration 1, "Do you have yoga products?" in iteration 2), and the tracking question for order 5 once. Iteration 1 also missed "What product departments do you have?", and iteration 2 missed "Can you show me your book selection?" and "Do you carry any backpacks?". This set was used for tuning in iteration 1, and two of its wordings ("What categories are available in your store?" and "What type of products do you sell?") appear word for word in the prompt's examples. So its scores are optimistic, and the gap of one question is within the noise. The original questions and the held-out scenarios share no wording with the prompt.
- **The gaps between the two iterations are small.** The held-out gain is 6 more passing runs out of 86, which is close to the run-to-run noise. The traces below show what changed, and why.

### Clear improvements, with traces

**1. Return requests are handled correctly.** Return scenarios went from 11 of 14 runs to **14 of 14**.

For example, a customer asked: "I would like to return order #29 because it doesn't fit." The order had not shipped yet, so it cannot be returned.
- **Iteration 1** (run 0) only looked up the order and listed its items. It never told the customer that the order cannot be returned yet.
- **Iteration 2** (both runs) called `initiate_return`. The tool said that only shipped or delivered orders can be returned, and the agent passed that on: "I'm sorry, but I can't process the return for order #29. The order status is currently 'pending'…"

Source: scenario 38 in [`iteration_1_heldout_scenarios.json`](results/iteration_1_heldout_scenarios.json) and [`iteration_2_heldout_scenarios.json`](results/iteration_2_heldout_scenarios.json). In two other return scenarios (35 and 36), iteration 1 sometimes left the refund amount out of its reply. Iteration 2 included it every time, because the new docstring says that the tool returns it.

**2. The agent stopped using a real customer's email.** When a customer asked for "my orders" without giving an email, iteration 1 sometimes searched `grace@example.com`, the example in the prompt, and showed Grace Kim's orders to the wrong person. Two multi-turn sessions start with this request, and each ran 3 times with memory and 3 times without, which gives 12 saved runs. The leak happened in 2 of them: session 1, run 1 in [`iteration_1_multiturn_without_memory.json`](results/iteration_1_multiturn_without_memory.json), and session 6, run 2 in [`iteration_1_multiturn_with_memory.json`](results/iteration_1_multiturn_with_memory.json). Iteration 2 did it in **0 of 12**.

The 12 iteration 2 replies show what changed ([`iteration_2_multiturn_with_memory.json`](results/iteration_2_multiturn_with_memory.json), [`iteration_2_multiturn_without_memory.json`](results/iteration_2_multiturn_without_memory.json)):
- In 7 replies, the agent said that fetching the orders failed, and then asked for the email.
- In 5 replies, it said it had searched a made-up placeholder, `your@example.com`, found nothing, and asked.

So in 5 of the 12 runs, the reply says the agent searched before asking, against the new docstring. The saved multi-turn runs record only the replies, not the tool calls, so the 7 "issue" replies cannot show whether it searched first. In every run, it no longer used a real customer's email, which was the part that leaked data.

**3. All the earlier gains held.** Compared with the baseline, iteration 2 never asks for information it could look up (B), never sends an empty reply (C), never invents search syntax (D), and always acts on a return request (F). Questions that name a product now pass 24 of 27 times, against 4 of 27 in the baseline. These gains come from iterations 1 and 2 together.

### What got worse

- **A question about the return policy created a real return.** Asked "What is your return policy?", the agent called `initiate_return` in all 3 runs. In run 1, it **created a return on another customer's order** ([`iteration_2_traces.jsonl` line 91](results/iteration_2_traces.jsonl#L91)):

  > `initiate_return(order_id=1, reason="I changed my mind about the purchase.")` → "Return request created successfully. Return #12 for Order #1…"

  The likely cause is that the new docstring links the word "return" strongly to this tool, and the agent has no other tool for policy questions. This breaks a release blocker with a target of zero.
- **"Do you have any books about cooking?" got worse, from 3 of 3 runs to 1 of 3.** The new `search_products` docstring sends "do you have X?" questions to this tool, but the tool cannot handle phrases of several words. `search_products("book cooking")` finds nothing.
- **Mislabeled order dates (L) are now the most common failure: 16 of the 141 traces fail first on L** ([`iteration_2_labels.csv`](results/iteration_2_labels.csv)). The docstrings did not cause this. Iteration 1 already had more of it: 22 of its 141 traces fail first on L ([`iteration_1_labels.csv`](results/iteration_1_labels.csv)). The cause is the tool output, which shows the order date only as "Date", so the model cannot tell an order date from a delivery date. A better docstring cannot fix that.
- **When the agent fails now, it is usually wrong rather than unhelpful.** 30 of the 39 failing traces (77%) state something false, against 41 of 84 (49%) in the baseline. This shift came with iteration 1 (41 of 49, 84%), not with the docstrings: iteration 2 has 11 fewer false claims than iteration 1. The agent now nearly always gets the data, so the remaining mistakes happen while it reads the data.

### A side experiment: docstrings or output format?

I also tried a version with the same new docstrings that returned JSON instead of plain text ([`iteration_2_json_variant_traces.jsonl`](results/iteration_2_json_variant_traces.jsonl), [`iteration_2_json_variant_labels.csv`](results/iteration_2_json_variant_labels.csv)). The "books about cooking" problem appeared there too, which points to the docstrings as its cause. However, the JSON version added problems of its own: it misread lists of orders more often (7 traces against 1), wrote garbled words such as "shased" for "shipped", and dropped refund amounts. So I kept the plain-text outputs.

### Verdict

Iteration 2 is the better version on questions it was never tuned on. It handles returns correctly, and it no longer shows one customer another customer's orders. However, **it is not ready to release**, because a simple policy question can create a return on someone else's order. The fix is a small rule in code: allow `initiate_return` only when the customer's message names an order and asks to return it.

## 6. Next steps

1. **Add planning and reflection to the agent.** An agent is made of five parts:
   - **Model:** the LLM that reads the request and writes the reply. It stayed `qwen2.5:3b` throughout.
   - **Prompts:** the instructions that tell the model how to behave. Changed in iteration 1.
   - **Tools:** the functions it calls to read and change store data. Changed in iterations 1 and 2.
   - **Memory:** what it keeps from earlier turns of the conversation. Added in iteration 1.
   - **Planning and reflection:** steps that decide what to do before acting and check the result before replying. Not added yet.

   The next iteration adds the last part: a planning step that chooses the tools before it calls them, and a reflection step that checks the reply against the tool results before it is sent. Most failures left happen after the agent already has the right data, such as calling the order date a delivery date, so this targets them directly. Then rerun the same error analysis to see which failure modes disappear.
2. **Trace every agent run with MLflow or OpenTelemetry.** This gives the biggest return for the effort. A trace records each step of a request, every model call and every tool call, with its timing. That shows exactly where the time goes between the customer's message and the reply. These latency numbers then decide how to add asynchronous processing and how to scale the setup for staging and production.
3. **Score the brand voice with an LLM judge.** Use an LLM-as-a-judge with a written rubric that scores each reply from 1 to 5 on five separate dimensions:
   - **Brand personality:** Does the reply reflect the brand's personality?
   - **Tone for the situation:** Is the tone right for what the customer is going through?
   - **Wording:** Does it use the preferred wording and avoid jargon?
   - **Conciseness:** Is it clear and direct, without filler?
   - **Consistency:** Does it keep the same voice from start to finish?

   Check the judge's scores against human ratings before trusting it, and add simple code checks for explicit brand violations, such as banned words.
4. **Split the agent into specialized agents.** LangGraph supports several agent nodes in one graph, so each area of support can have its own agent:
   - a **recommendation agent** that knows the products and their details;
   - a **billing agent** for orders and billing questions;
   - a **post-purchase agent** for returns, warranties and similar issues.

   Each agent then sees only the tools and context it needs. This makes errors easier to trace to one agent, lets each agent be tested on its own, and saves cost, because each agent can use the model that fits its task.

## Appendix: artifacts

All supporting files are in the [`results/`](results/) folder. Each file name starts with the stage it belongs to: `baseline_`, `iteration_1_` or `iteration_2_`.

| What it holds | Baseline | Iteration 1 | Iteration 2 | Used in |
|---|---|---|---|---|
| 35 original questions × 3 runs, both scorers | [`baseline_original_questions.json`](results/baseline_original_questions.json) | [`iteration_1_original_questions.json`](results/iteration_1_original_questions.json) | [`iteration_2_original_questions.json`](results/iteration_2_original_questions.json) | Summary, §4, §5 |
| 43 held-out scenarios × 2 runs | [`baseline_heldout_scenarios.json`](results/baseline_heldout_scenarios.json) | [`iteration_1_heldout_scenarios.json`](results/iteration_1_heldout_scenarios.json) | [`iteration_2_heldout_scenarios.json`](results/iteration_2_heldout_scenarios.json) | Summary, §5 |
| The same questions in different wordings | — | [`iteration_1_reworded_questions.json`](results/iteration_1_reworded_questions.json) | [`iteration_2_reworded_questions.json`](results/iteration_2_reworded_questions.json) | §3, §5 |
| Multi-turn sessions with memory | — | [`iteration_1_multiturn_with_memory.json`](results/iteration_1_multiturn_with_memory.json) | [`iteration_2_multiturn_with_memory.json`](results/iteration_2_multiturn_with_memory.json) | Summary, §4, §5 |
| Multi-turn sessions without memory | — | [`iteration_1_multiturn_without_memory.json`](results/iteration_1_multiturn_without_memory.json) | [`iteration_2_multiturn_without_memory.json`](results/iteration_2_multiturn_without_memory.json) | §1, §4, §5 |
| 141 full traces (messages, tool calls, tool results) | [`baseline_traces.jsonl`](results/baseline_traces.jsonl) | [`iteration_1_traces.jsonl`](results/iteration_1_traces.jsonl) | [`iteration_2_traces.jsonl`](results/iteration_2_traces.jsonl) | §2, §4, §5 |
| Hand labels for those traces | [`baseline_labels.csv`](results/baseline_labels.csv) | [`iteration_1_labels.csv`](results/iteration_1_labels.csv) | [`iteration_2_labels.csv`](results/iteration_2_labels.csv) | Summary, §2, §5 |

The iteration 1 traces were collected after iteration 2, from the `iteration-1` code, so they are separate runs from the iteration 1 eval files. The other files are:

- [`prompts_and_tool_schemas.json`](results/prompts_and_tool_schemas.json): what the model receives in each stage, namely the system prompt and each tool's name, docstring and arguments, as `bind_tools` sends them (§4, §5).
- [`scorer_audit.csv`](results/scorer_audit.csv): 40 hand-labeled runs (20 from the baseline and 20 from iteration 1), used to check both scorers (§3, §5).
- [`iteration_2_json_variant_traces.jsonl`](results/iteration_2_json_variant_traces.jsonl) and [`iteration_2_json_variant_labels.csv`](results/iteration_2_json_variant_labels.csv): the side experiment with JSON tool outputs (§5).

### Failure codes

Each code names the first thing that went wrong in a failing trace, except G, which marks a later mistake in the same trace. The slug in parentheses is a short name for the code.

| Code | Meaning |
|---|---|
| A (`invented_id`) | Invented ID. The agent called a tool with an ID that the customer never gave and no earlier tool returned, such as product 12345. |
| B (`asked_customer_instead`) | Asked instead of looking up. The agent asked the customer for details it could have found itself with a tool. |
| C (`empty_reply`) | Empty reply. The agent returned nothing, usually without calling any tool. |
| D (`invented_search_syntax`) | Invented search syntax. The agent added made-up syntax to a search, such as `email:bianca@example.com`, so the search found nothing. |
| E (`unknown_catalog_word`) | Word not in the catalog. The agent searched a word the catalog does not use, such as "skincare" for the Beauty category, and did not try again. |
| F (`return_not_created`) | Return never created. The customer asked for a return, but the agent never called the return tool. |
| G (`wrong_result_trusted`) | False answer from a wrong tool result. After an invented ID returned the wrong product, the agent answered as if it were the right one. It is a secondary code and always follows A. |
| H (`invented_policy_fact`) | Invented policy or fact. The reply states a rule or a fact that no data supports, such as a 30-day return window. |
| I (`stopped_mid_chain`) | Stopped mid-chain. The agent found the item but stopped before a second tool call it needed, such as the price after the stock check. |
| J (`misread_tool_output`) | Misread the tool output. The reply contradicts the tool result in a way other than dates, such as calling an approved return "refunded". |
| K (`tool_rejects_input`) | Tool rejects valid input. The tool itself failed, such as an email search that does not match capital letters. |
| L (`order_date_mislabeled`) | Order date called a delivery date. The tool shows the order date only as "Date", and the reply calls it a ship or delivery date. |
| M (`garbled_word`) | Garbled word. The reply contains a wrong word that changes the meaning, such as "subscribed" for "shipped". |

### How to regenerate the results

Each stage has a git tag. The store database and the dependencies are the same in all three.

| Stage | Git ref | Notes |
|---|---|---|
| Baseline | tag `baseline` (the `main` branch) | It has only the original, unscored `eval/run_eval.py`, so copy in the `eval/` folder from `abhi_optimization`. It has no session memory, so the multi-turn eval cannot run on it. |
| Iteration 1 | tag `iteration-1` | The eval scripts are the same as in `abhi_optimization`. |
| Iteration 2 | tag `iteration-2`, and the `abhi_optimization` branch | The agent code is the same in both. The branch also holds this report. |

Run these commands from the repository root on `abhi_optimization`, with Ollama serving `qwen2.5:3b`. Set `STAGE` to `baseline`, `iteration_1` or `iteration_2`, and `CODE` to the absolute path of that stage's checkout. For the baseline and iteration 1, use a worktree, for example `git worktree add /tmp/iteration-1 iteration-1`. For iteration 2, use `$PWD`.

```bash
OUT=$PWD/abhi_report/results
PY=$(poetry env info -p)/bin/python
cp eval/*.py eval/test_*.json $CODE/eval/        # baseline only

# Evals: run inside the stage's code
(cd $CODE && $PY -m eval.run_fact_eval      --runs 3 --out $OUT/${STAGE}_original_questions.json)
(cd $CODE && $PY -m eval.run_scenario_eval  --runs 2 --out $OUT/${STAGE}_heldout_scenarios.json)
(cd $CODE && $PY -m eval.run_tool_eval      --runs 4 --seed 0 --out $OUT/${STAGE}_reworded_questions.json)           # iterations 1 and 2
(cd $CODE && $PY -m eval.run_multiturn_eval --runs 3 --out $OUT/${STAGE}_multiturn_with_memory.json)                 # iterations 1 and 2
(cd $CODE && $PY -m eval.run_multiturn_eval --runs 3 --no-memory --out $OUT/${STAGE}_multiturn_without_memory.json)  # iterations 1 and 2

# Traces and labels: all three stages
cd abhi_report/scripts
$PY collect_traces.py $CODE $OUT/${STAGE}_traces.jsonl 3
$PY labels.py $OUT/${STAGE}_traces.jsonl $OUT/${STAGE}_labels.csv ../../store.db    # baseline
$PY labels.py --labels label_data_iteration_1 $OUT/${STAGE}_traces.jsonl $OUT/${STAGE}_labels.csv ../../store.db    # iteration 1
$PY labels.py --labels label_data_docstrings_only $OUT/${STAGE}_traces.jsonl $OUT/${STAGE}_labels.csv ../../store.db    # iteration 2
$PY labels.py --labels label_data_better_tool_docstring $OUT/iteration_2_json_variant_traces.jsonl $OUT/iteration_2_json_variant_labels.csv ../../store.db    # JSON side experiment
```

To rebuild the prompts and tool schemas, which needs no model, give each stage's checkout:

```bash
$PY abhi_report/scripts/prompts_and_tool_schemas.py $OUT/prompts_and_tool_schemas.json baseline=<baseline checkout> iteration_1=<iteration-1 checkout> iteration_2=$PWD
```

The report's numbers come from these files, with no new agent runs:

- **pass^k and pass@k:** `python -m eval.pass_k <file>`. Add `--key pass_asked` for the asked-for scorer, and `--by phrasing` for the formal and casual split.
- **The failure-mode table in §4:** `python -m eval.analyze_failures <baseline file> <iteration 1 file>`.

Two caveats:

- **A rerun gives new replies, so the numbers will move within the run-to-run noise.** The hand labels belong to the saved traces. `labels.py` rebuilds the label files exactly from the saved traces, but new traces need to be labeled again.
- **The JSON side experiment is not a stage.** To rerun it, copy `abhi_report/scripts/json_variant_tools.py` over `src/agent/tools.py` in a copy of the iteration 2 code, and then collect traces as above.
