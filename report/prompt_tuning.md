# Prompt Tuning and the Store-Catalog Tool

This report covers one workstream of the challenge: tuning the system prompt of the ShopEasy support agent, and adding a tool so the agent can answer "what do you sell?" questions. It walks through each step in the order it happened, what was checked at each step, and what the results showed.

- **Model:** `qwen2.5:3b` served by Ollama. The model was not changed, as the challenge requires.
- **Agent:** LangGraph `create_react_agent` (`src/agent/graph.py`) with the tools in `src/agent/tools.py`.
- **Files changed:** `src/agent/prompts.py` (system prompt), `src/agent/tools.py` (new `list_categories` tool; `get_product_details` and `check_inventory` now accept a product name), and the new tool-call eval in `eval/run_tool_eval.py` and `eval/test_tool_queries.json`.

---

## 1. Summary

- **New tool.** `list_categories` lists the in-stock categories with product counts and price ranges, or the in-stock products in one category. Before this, the agent had no way to answer "what categories do you have?" and replied that it couldn't find anything.
- **New prompt.** The original 5-line prompt was replaced with a short set of rules plus a "Which tool to call" section. That section maps example customer questions to the exact tool calls they need, with one entry per tool.
- **Result on the existing 35-query eval set** (2 runs per prompt, scored on key facts such as prices, tracking numbers and stock counts):

| Prompt version | Key facts found | Empty replies |
|---|---|---|
| Original prompt (with the new tool available) | 76/156 (49%) | 1/70 |
| V1: rules plus catalog question → tool mappings only | 68/156 (44%) | 3/70 |
| V2: one mapping entry per tool | 89/156 (57%) | 1/70 |
| V3: V2 plus multi-step headings and a category-retry rule (rejected) | 85–86/156 (55%) | 5–6/70 |
| V5: V2 plus the `list_categories` fix for the book questions | 92/156 (59%) | 0/70 |
| V6: V5 plus keyword matching in `list_categories` | 104/156 (67%) | 0/70 |
| **V7: V6 plus product tools that accept a name (final, section 4)** | **114/156 (73%)** | **0/70** |

- **Clearest gains (V2 vs original):** looking up all orders by email (20/32 → 32/32) and product price and details (2/8 → 7/8). Shipping also improved, but only slightly (8/10 → 10/10).
- **Regression:** order status dropped from 6/6 to 4/6.
- **Still failing:** stock questions that name a product (5/34) and broad product searches like "outdoor gear" or "skincare" (0/28). On these questions, the model nearly always made a single tool call. For stock questions, that call was `check_inventory` with a guessed ID, when it needed to find the ID with `search_products` first. None of the three prompt versions tried changed this, so the top next step is a tool change (section 9). **V7 made that tool change** (see below).
- **Tool-call eval (section 4).** A new eval asks each tool's question in 4–5 different wordings and checks that the answer is the same. It showed that "What books do you have?"-style questions never listed the books (0/12 in a probe). Making `list_categories`'s argument required, matching categories loosely, adding no-match fallbacks, and adjusting the prompt's catalog entry fixed this (12/12). Two later manual checks led to two more tool fixes. Keyword matching made "yoga gear" find the yoga products (V6). Letting `get_product_details` and `check_inventory` accept a product name stopped the guessed IDs, such as the "Vacuum Insulated Tumbler (product ID 123)" answer (V7). Tool-eval passes rose from 78% to 95%, and the 35-query score from 89 to 114 facts. Open issues are listed in section 4.8.
- **Why the tools were changed, not just the prompt (section 5).** On the main branch, name-based product questions failed 12/12: the model invented IDs such as `123` instead of searching first. Even a step-by-step prompt with worked examples got it to search and then use the ID in only 2 of 24 runs. Product tools that accept a name passed 48/48.

---

## 2. Understanding the data first

Before changing the agent, I traced how the data is created, so I knew what the agent can and cannot know.

- **`src/data/seed.py`** is not imported by any code. It runs only through `poetry run seed-db` (`pyproject.toml`). It wipes and refills all 6 tables in `store.db`: 30 customers, 170 products, 76 orders, 188 order items, 66 shipping records and 11 returns.
- **`src/data/database.py`** defines the schema. Every agent tool reads `store.db` through `get_connection()`.
- **Gaps that matter for the agent:**
  - **No ratings or reviews.** Products have only `name, category, price, description, stock_quantity`. A question like "what are the best X?" cannot be answered from the data. The agent should say so instead of inventing a ranking.
  - **`customers.created_at` and `returns.created_at` are never set by the seed script.** They default to the time the seed ran. In the current `store.db`, every customer and every return is stamped 2026-10-02. Orders are dated Oct 2025 to Apr 2026, so customers appear to have signed up after ordering, and returns appear to be filed months after delivery.
  - **Every product currently has stock.** The seed data gives each product at least 15 units, and no tool reduces stock.
  - **`initiate_return` writes to the database.** Any eval run that triggers it changes `store.db`. This shaped how evals were run later (section 7).

---

## 3. Step by step

### Step 1: Diagnose the catalog-question failure

A new customer asked:

> **You:** tell me what categories of boots you have?
> **Agent:** I couldn't find any boots in the system with the specified category…

- **Finding:** none of the 7 original tools could describe the catalog. `search_products` only does a `LIKE` match on name or category, and it needs a search term. The agent had no way to list categories.

### Step 2: Add a minimal `list_categories` tool

- **First version:** no arguments. It returns every category with its product count and price range, using a single `GROUP BY` query.
- **Check (live agent):**
  - "what do you sell?" → correct list of all 10 categories.
  - "what categories of boots…?" → the agent called the tool, but then listed every category as if they were boots. Category counts alone don't tell it which boots exist.
- **Change:** added an optional `category` argument. With a category name, the tool returns that category's products with IDs and prices.
- **Check:**
  - "what do you have in the footwear category?" → all 15 footwear products, correct.
  - The boots question now pointed to Footwear but still didn't list the boots. Answering it fully needs two calls in a row (all categories, then Footwear), and the model stopped after the first. This was the first sign of the chaining weakness that comes back in Step 9.

### Step 3: Show only products that are in stock

- **Change:** added `stock_quantity > 0` to both queries. Out-of-stock products are hidden, and a category with nothing in stock disappears. The empty-result message became "No in-stock products in a category named 'X'…", so a sold-out category is not reported as missing.
- **Check:** because every seeded product has stock, I tested on a scratch copy of the DB, with all Books and two boots set to 0. Books disappeared from the list, Footwear dropped from 15 to 13 products, and the two boots were no longer listed. The real `store.db` was not touched.

### Step 4: First prompt iteration (rule, tool description, two full examples)

- **Change:** added a "Store catalog questions" section. It said to always call `list_categories` and never answer from memory, described the tool's two modes, and gave two full examples: question → tool call → tool output → reply. The two questions were "What categories are available in your store?" and "What type of products do you sell?".
- **Check (live agent, tool calls recorded):**

| Question | Tool called | Result |
|---|---|---|
| "What categories are available in your store ?" | `list_categories()` | All 10 categories |
| "what type of products do you sell ?" | `list_categories()` | All 10 categories |
| "tell me what categories of boots you have ?" | `list_categories()` | Points to Footwear, but doesn't list the boots |
| "what do you guys have?" | none | Vague reply with no data |

- **Finding:** the target questions worked. The tool output in the examples was deliberately shortened with "…", and the agent used the real tool data rather than copying it. Casual wording and two-step questions still failed.

### Step 5: Describe the examples as teaching material

- **Change:** reworded the instruction so the examples are described as teaching the pattern to follow (recognize the question, call the tool, present the result), not as a source of data.
- **Check:** both target questions still called the tool and listed all 10 categories.

### Step 6: Concise rewrite, which caused a regression

- **Change:** rewrote the prompt to remove repeated instructions: 3 numbered rules, a `## Tools` section holding the tool description, and the two examples.
- **Check:** the catalog questions still worked, but I also ran an unrelated question, "where is my order #2?". It came back as an **empty reply with no tool call**. That question had not been tested before this point.
- **Comparing with the original prompt:** the original prompt called `lookup_order` 3 out of 3 times. The new prompt returned nothing 3 out of 3 times. So the rewrite caused it.
- **Root cause:** the model generated 22 tokens, but none came back as text or as a tool call. I sampled the model's raw output, bypassing Ollama's tool-call parser. It mostly produced `<tool_call>{"name": "get_order_status", …}</tool_call>` (and once `get_order_details`). The model had **invented tools that don't exist**. Because those calls never reach the agent, the reply comes back empty. Ollama dropping unknown tool calls was inferred from this; it was not confirmed directly.
- **Renaming the `## Tools` heading to `## Question types`** did not help: the full agent still gave empty replies 2 out of 2 times.
- **Testing parts of the prompt one at a time** (6 samples each, first tool call recorded). These probes used a hand-built copy of the chat template. Step 7 shows that this method can disagree with Ollama's real endpoint, so read these results as a direction, not exact rates.

| Prompt variant | First tool call on "where is my order #2?" |
|---|---|
| Original prompt | `lookup_order` 6/6 |
| Full new prompt | `get_order_status` (invented) 6/6 |
| Rules only (question-type section removed) | `lookup_order` 6/6 |
| Rules removed (role and examples kept) | invented 3/6, `lookup_order` 3/6 |
| Examples removed (section text kept) | `lookup_order` 6/6 |

- **Finding:** removing the examples fixed the invented names, so the full examples were the trigger. One possible explanation, not tested on its own, is that the examples showed only one tool in a plain-text format (`Call: list_categories()`).
- **Formats tested for the examples** (same hand-built probe, followed by full-agent runs where noted):

| Example format | "where is my order #2?" | "what type of products do you sell?" |
|---|---|---|
| Plain text `Call: …` / `Result: …` | invented names (6/6 above) | calls `list_categories` |
| Native `<tool_call>` / `<tool_response>` JSON (the model's own format) | `lookup_order` 6/6; full agent 2/2 | probe: tool 4/5; **full agent: skipped the tool 2/2** |
| Plain text plus a rule listing the exact tool names | `lookup_order` 6/6 | tool 3/3 in one probe, but no tool 5/5 in a later probe |

- **Problem with the native format:** in both full-agent runs of "what type of products do you sell?", the model **skipped the tool and repeated the shortened example reply word for word** (only Electronics and Footwear). The likely reason is that examples in the model's own tool-call format look like earlier turns of a real conversation.

### Step 7: Question-to-tool mapping plus an exact tool-name rule (V1)

- **Change:** replaced the full examples with one-line mappings: `"What type of products do you sell?" -> list_categories()`. There is no sample tool output or reply, so there is nothing to copy. I also added rule 1: "Call only these tools, using their exact names: …". The name list is built from `ALL_TOOLS`, so a new tool is listed automatically.
- **A testing lesson.** The hand-built probe said the mapping-only prompt was fine for the order question (`lookup_order` 5/5). Through Ollama's real `/api/chat` endpoint, which uses the real template and tool-call parser, the result was different: "where is my order #2?" came back empty 4 out of 6 times, and "what's the status of order 5?" 3 out of 6. **From then on, every check used the real endpoint or the full agent.**
- **Check (real endpoint, 5 samples per question, first tool call recorded).** For the product and stock rows, the customer gave a name, not an ID. So a first call to `get_product_details` or `check_inventory` means the model passed a guessed ID instead of searching first.

| Question | Original prompt | Mapping only | **Mapping + name rule (V1)** |
|---|---|---|---|
| "where is my order #2?" | `lookup_order` 5/5 | empty 1/5 | `lookup_order` 5/5 |
| "what's the status of order 5?" | empty 2/5 | empty 5/5 | `get_shipping_status` 5/5 |
| "what type of products do you sell ?" | `list_categories` 5/5 | 5/5 | 5/5 |
| "What categories are available…" | 5/5 | 5/5 | 5/5 |
| "what do you guys have?" | no tool 5/5 | `list_categories` 5/5 | `list_categories` 5/5 |
| "How much is the Leather Messenger Bag?" | guessed ID 3/5, searched 2/5 | guessed ID 3/5 | guessed ID 4/5 |
| "Is the yoga mat in stock?" | guessed ID 5/5 | guessed ID 5/5 | guessed ID 5/5 |
| Return request for order #14 | `initiate_return` 4/5 | 5/5 | 5/5 |

- **Finding:** V1 had no empty replies in this probe and now handled casual wording. It also fixed a failure the original prompt already had ("status of order 5" was empty 2 out of 5 times). Product and stock questions were still weak under every version: the model passed a guessed ID instead of searching first.

### Step 8: One entry per tool, measured on the full eval set (V2)

- **Change:** added a "Which tool to call" entry for every tool, plus rule 4: "Never guess an ID. If the customer names a product, call search_products first."

| Entry | Example mapping |
|---|---|
| What the store sells | `"What gadgets do you have?" -> list_categories(category="Electronics")` |
| Finding a product by name | `"Do you sell headphones?" -> search_products(query="headphone")` |
| Product price or details | `search_products(...)`, then `get_product_details(product_id=<id>)` |
| Stock levels | `search_products(...)`, then `check_inventory(product_id=<id>)` |
| One order's date, items, or total | `lookup_order(order_id=31)` |
| Order status | `lookup_order` then `get_shipping_status` |
| Shipping, tracking, delivery | `get_shipping_status(order_id=22)` |
| All orders for a customer | `search_orders(query="grace@example.com")` (ask for the email if missing) |
| Returns | `initiate_return(order_id=38, reason="pants don't fit")` |

- **Avoiding leakage into the test:** no example reuses an eval query's wording, order number or customer email. One overlap remains: the stock example uses Trail Hiking Boot, which is also the subject of a return query (#18), though that query asks something different. Otherwise the model could score well just by copying answers.
- **Eval harness:** this is when I moved from spot checks to the full eval set (section 7 describes the method).

| Category (key facts) | Original | V1 | **V2** |
|---|---|---|---|
| order_lookup | 20/32 | 20/32 | **32/32** |
| order_details | 29/32 | 27/32 | 29/32 |
| order_status | 6/6 | 5/6 | 4/6 |
| shipping | 8/10 | 10/10 | **10/10** |
| product_info | 2/8 | 3/8 | **7/8** |
| returns | 1/6 | 2/6 | 2/6 |
| inventory | 6/34 | 1/34 | 5/34 |
| product_search | 4/28 | 0/28 | 0/28 |
| **Total** | **76/156 (49%)** | **68/156 (44%)** | **89/156 (57%)** |

- **Finding:** V2 has the highest total. Its clearest gains are email lookups (20/32 → 32/32) and product details (2/8 → 7/8). It regressed on order status (6/6 → 4/6), and inventory and product_search stayed low.
- **V1 scored below the original overall** (68 vs 76). The gap comes mostly from inventory (1/34 vs 6/34) and product_search (0/28 vs 4/28), while V1 did better on shipping, product_info and returns. V2 differs from V1 in two ways, the extra entries and rule 4, so this data can't separate their effects.

### Step 9: Try to fix the remaining two categories (V3, rejected)

- **Looking at the misses:**
  - **inventory:** the model called `check_inventory` directly with a guessed ID instead of searching first. The guessed ID belonged to a different product, so the reply reported that product's stock. For example, it said "80 Portable Phone Chargers" when the real number is 200, and one reply even mentioned "Insulated…", another product with 80 units. In other replies it cited a made-up ID ("product ID 123") and called an in-stock product out of stock.
  - **product_search:** for "outdoor gear", "skincare" and "fitness equipment" questions, the model called `list_categories` but never got a product list. Some replies suggest it passed a category name that doesn't exist (for example "there might be a category name mismatch" for skincare). Only tool names were recorded, not arguments, so this is inferred. "Do you sell sunglasses?" went to `list_categories` instead of `search_products`. "Do you have any books about cooking?" did call `search_products`, but found nothing.
- **Change (V3):** the headings named the full sequence of calls ("Stock levels -> search_products, then check_inventory"). I added a two-step catalog example ("beach trip"), a rule to retry with the closest category name when a category returns nothing, and an instruction to include product names and prices.
- **Check (2 runs, done twice):** 85/156 and 86/156, which is no better than V2, and empty replies rose to 5–6/70. **I reverted to V2.**
- **Tool-call sequences on inventory and product_search queries:**

| Prompt | Most common call sequences |
|---|---|
| Original | `list_categories` ×9, `check_inventory` ×6, `search_products` ×2 |
| V2 | `list_categories` ×10, `check_inventory` ×6, `search_products` ×2, `check_inventory → search_products → check_inventory` ×2 |
| V3 | `list_categories` ×9, `check_inventory` ×7–8, `search_products` ×3 |

- **Finding:** on these queries, under all three prompts, the model nearly always made **one** call and answered from it. None of the wordings tried got it to search for an ID first and then use it. That points to a tool change rather than more prompt changes (section 9).

---

## 4. Tool-call evals and the tool fixes (V4–V7)

The 35-query eval set checks facts, but it doesn't show whether the agent gives the **same answer to the same question asked in different words**. I added a tool-specific eval for that, then used it to fix the "products in one category" questions.

### 4.1 The tool-call eval

- **Files:** `eval/test_tool_queries.json` (data) and `eval/run_tool_eval.py` (runner).
- **Structure:** one benchmark per tool, built with the requested dataclass:

  ```python
  @dataclass
  class ToolCallBenchmark:
      name: str            # the tool, e.g. "list_categories"
      examples: list[dict] # entries from test_tool_queries.json
      scorer: Callable     # lambda (answer, example) -> score in [0, 1]
  ```

- **Data:** 16 entries, 2 per tool. Each entry holds 4–5 paraphrases that must all produce the same answer (`questions`), a reference reply (`expected_answer`), and the facts the scorer looks for (`must_contain`). For example, entry 2 asks "What books do you have?", "Can you show me your book selection?", "Which books are available in your store?" and "I'm looking for something to read. What books do you carry?". All four must return the same 12 titles.
- **Expected values** were read from `store.db`. The entries use orders, emails and products that do not appear in the prompt's examples, so the prompt can't leak answers. For `get_product_details` and `check_inventory`, one entry asks by ID (it tests the tool) and one by name (it tests whether the agent searches for the ID first).
- **Scorer:** each benchmark's lambda returns the fraction of `must_contain` facts found in the reply. Matching ignores case, curly apostrophes and "&" versus "and". A number must not be part of a larger number, so "60" does not match "$49.60" or "160".
- **Runner:** for each entry, it picks distinct random paraphrases, sends each one to the agent on a fresh copy of `store.db` (because `initiate_return` writes rows), records the tools called, and scores the reply. The summary reports:
  - **Score:** the mean fraction of facts found.
  - **Pass:** all facts found.
  - **Tool hit:** the benchmark's tool was called.
  - **Empty:** replies with no text.
- **Usage:** `python -m eval.run_tool_eval --runs 4` asks every paraphrase once. `--benchmark NAME` runs one tool and `--out FILE` saves per-run results.

### 4.2 Baseline: the same question gave different answers

The first run (V2 prompt, 2 picks per entry) scored **78% (25/32 passes)**. Order, shipping, email-lookup and return benchmarks passed every time. The catalog benchmarks did not:

| Benchmark | Score | Pass | Tool hit |
|---|---|---|---|
| list_categories | 50% | 2/4 | 4/4 |
| search_products | 25% | 1/4 | 1/4 |
| get_product_details | 100% | 4/4 | 2/4 |
| check_inventory | 50% | 2/4 | 4/4 |

A manual chat session showed the problem on the book questions. Each question below was a separate, single-turn call:

| Question | Agent reply |
|---|---|
| "Which books are available in your store?" | Only the summary line: "Books: 12 products, $12.99–$44.99". |
| "What books do you have?" | "The store does not sell books." |
| "Can you show me your book selection?" | All 10 categories. |
| "tell me what all books do you have ?" | All 12 titles (correct). |

### 4.3 Root cause

A probe (3 samples per paraphrase, tool calls and arguments recorded) found that **all 12 runs called `list_categories({})`** with no category. That call returns only the category summary, and the model never made a second call to get the titles. Three things pushed it toward the call with no argument:

- **The argument was optional** (`category: str = ""`), so calling the tool with no argument was a valid choice.
- **The prompt said** "If unsure which category fits, call list_categories() first."
- **The only example that passed a category** used the word "Footwear" itself ("What do you have in Footwear?"). Nothing showed a customer's everyday word ("books", "toys") being passed as the category. The tool also matched the category exactly, so `category="book"` would have failed anyway.

### 4.4 Variants tested

The "Books" column is the 4 book paraphrases × 3 samples. The "Overview" column is the 5 paraphrases of entry 1 ("What categories are available…", "What type of products…", "What kinds of things can I buy here?", "Can you give me an overview…", "What product departments do you have?") × 3 samples.

| Variant | Books | Overview | Kept? |
|---|---|---|---|
| V2 (baseline) | 0/12 | not probed (2/2 in the eval run) | – |
| A: new prompt lines ("pass that kind as the category") and loose matching; argument still optional | 6/12 | not probed | No |
| B (V4): A plus a **required** `category` argument, with `"all"` for the overview | 12/12 | 2/4 in the eval run | Yes |
| C (V5): B plus the no-match fallbacks (section 4.5); kept and extended in V6 and V7 (section 4.6) | 4/4 in the eval run | 9/15 | Yes |
| D: C with a default `category="all"` | 4/12 | 15/15 | No |
| E: C plus the prompt rule "Always pass a category. Use "all" for an overview." | 12/12 | 6/15 | No |

- **The trade-off:** an optional argument lets the overview questions work but makes the model drop the category on the book questions (D). A required argument gets the book questions right, but the model sometimes still calls the tool with no argument. That call fails validation, and the agent tells the customer there was "an issue" (C). Telling the model to always pass the argument made this worse (E).
- **Why C was chosen:** the book questions are the target of this fix, and C passed all of them. The two original catalog questions ("What categories are available in your store?" and "What type of products do you sell?") passed 6/6 in C's overview probe. The misses were "What kinds of things can I buy here?" (1/3), "Can you give me an overview…" (2/3) and "What product departments do you have?" (0/3).

### 4.5 Changes for the book questions (V5)

**Tool definition: `list_categories` in `src/agent/tools.py`**

| Change | Before | After | Why |
|---|---|---|---|
| Signature | `category: str = ""` (optional) | `category: str` (required); `"all"` returns the overview | With an optional argument, the model left it out for the book questions (0/12 and 4/12). |
| Docstring | "With no argument, returns every product category…" | "Pass a category or kind of product (e.g. "Footwear", "books", "toys")… Pass "all" to get every category…" | The model reads the docstring as the tool description, so it now says the argument is expected. |
| Category matching | Exact, case-insensitive (`category LIKE 'Footwear'`) | Lowercased, a trailing "s" removed from words longer than 3 letters, and a substring match (`LIKE '%book%'`) | Customer words like "books", "Book" and "toys" now find "Books" and "Toys & Games". |
| Fallback 1 | "No in-stock products in a category named 'X'…" | If no category matches, return in-stock products whose **name** matches ("In-stock products matching 'yoga': …") | Under V4, "Do you sell backpacks?" and the yoga questions went to `list_categories("backpacks")` / `("yoga")` and got nothing. Now that call finds Camping Backpack 60L and the two yoga products. |
| Fallback 2 | – | If nothing matches, return the full category list with the header "'X' is not a category or product name. Here are all store categories:" | Under V4, "departments" and "overview" questions passed a category that matched nothing. Now they still get the list. |

**Prompt: the "What the store sells" entry in `src/agent/prompts.py`**

Before (V2):
```
### What the store sells -> list_categories
- "What categories are available in your store?" -> list_categories()
- "What type of products do you sell?" -> list_categories()
- "What do you have in Footwear?" -> list_categories(category="Footwear")
- "What gadgets do you have?" -> list_categories(category="Electronics")
If unsure which category fits, call list_categories() first. After answering, offer to show the products in a category.
```

After (V5):
```
### What the store sells -> list_categories
- "What categories are available in your store?" -> list_categories(category="all")
- "What type of products do you sell?" -> list_categories(category="all")
When the customer asks which products of a kind you have, pass that kind as the category:
- "Which toys do you sell?" -> list_categories(category="toys")
- "I need new clothes. What clothing do you carry?" -> list_categories(category="clothing")
- "What gadgets do you have?" -> list_categories(category="Electronics")
After listing categories, offer to show the products in one.
```

- **Overview examples** now pass `"all"`, to match the required argument.
- **Removed** "If unsure which category fits, call list_categories() first", which pushed the model toward the call with no argument.
- **Added** a rule and two examples where the customer's own word is passed as the category ("toys", "clothing"). These rely on the loose matching. The examples use Toys and Clothing, not Books, so the book entry in the eval stays unseen. The rest of the prompt is unchanged from V2.

### 4.6 Follow-up fixes from manual checks (V6, V7)

After V5, manual chat sessions on two more entries showed answers that were not meaningful.

**V6: "yoga gear" found nothing (entry 3)**

| Question | Agent reply (manual session) |
|---|---|
| "Do you sell anything for yoga?" | "It seems there are no yoga products available at the moment…" |
| "Do you have yoga products?" | Listed all categories, then "there are no yoga products in the 'Fitness' category". |
| "Any yoga gear in your shop?" | "There might not be a specific category called 'yoga gear'…" |

- **Probe on V5** (3 samples per paraphrase, arguments recorded): 10/12 runs passed `category="yoga"` and listed both yoga products. The 2 failures passed the whole phrase, `category="yoga gear"`. That phrase matched no category and no product name, so the tool returned the category list, and the agent said it had no yoga gear.
- **The first two replies above** echo an older no-match message ("…call list_categories…"). The chat session was probably started before the V5 fallbacks were added, since a running process keeps the old code. Restart `poetry run chat` after any tool change.
- **Change:** `list_categories` now matches on **keywords** rather than the whole phrase:
  - the input is split into words, and a trailing "s" is removed from each word;
  - filler words that customers add around a product type are dropped ("gear", "products", "items", "stuff", "equipment", "anything", "for", …);
  - a category matches if it contains any keyword. Otherwise, products whose name contains a keyword are listed, best matches first.
  - Now "yoga gear", "yoga products" and "anything for yoga" all return the 2 yoga products, and "fitness equipment" returns the Fitness category.
- **Check:** 12/12 yoga runs and 12/12 backpack runs got the right products from the tool. In 2 yoga replies, the model shortened "High-Waist Yoga Leggings" to "Yoga Leggings". The answer is meaningful, but the strict scorer counts the name as missing.

**V7: product price by name guessed IDs (entry 6, and entry 8 for stock)**

| Question | Agent reply (manual session) |
|---|---|
| "How much does the Vacuum Insulated Tumbler cost?" | "I seem to have encountered an issue parsing the product ID. Could you please provide the ID…" |
| "How much does the Vacuum Insulated Tumbler cost?" (asked again) | "The Vacuum Insulated Tumbler (product ID 123) is called an Insulated Cooler Bag 24-Can… costs $39.99." |
| The other three paraphrases | "$24.99" (correct, read from a `search_products` result) |

- **Cause:** this is the chaining weakness from Step 9. `get_product_details` and `check_inventory` took only `product_id: int`. The model either passed the name (which fails validation, hence "issue parsing the product ID") or guessed an ID ("123" is the Insulated Cooler Bag). It did not call `search_products` first, despite rule 4 and the two-step examples. The Kettlebell stock replies ("65 units", which is the Waterproof Rain Boots' count) had the same cause.
- **Change (tools):** both tools now take `product: str`, which can be an ID or a name. A shared helper, `_find_products`, resolves it:
  - "33", "#33", "product 33" and "Product ID 33" are looked up as ID 33;
  - otherwise, an exact name match (ignoring case) is returned if there is one;
  - otherwise, it returns the products whose names share the most keywords with the input, at most 5.
  - The docstrings now say "Pass the product's ID (e.g. "33") or its name (e.g. "Vacuum Insulated Tumbler")."
- **Change (prompt):**
  - Rule 4 became "Never guess an ID. If the customer names a product, pass the product name instead."
  - The two-step examples became single calls: `get_product_details(product="Ceramic Coffee Mug")`, `get_product_details(product="20")`, `check_inventory(product="Trail Hiking Boot")`, and a new `check_inventory(product="12")`.
- **Check:** 48/48 probe runs on entries 5–8 (by ID and by name, 4 paraphrases × 3 samples each) made one call with the right argument and gave the right price or stock count. None guessed an ID.

### 4.7 Results

**Tool-call eval** (V5–V7: every paraphrase asked once, 64 runs. V2: the first run, 32 runs, where paraphrases could repeat):

| Benchmark | V2 pass | V5 pass | V6 pass | **V7 pass** | V7 score | V7 tool hit |
|---|---|---|---|---|---|---|
| list_categories | 2/4 | 7/8 | 7/8 | **8/8** | 100% | 8/8 |
| search_products | 1/4 | 6/8 | 7/8 | **6/8** | 81% | 0/8 |
| get_product_details | 4/4 | 7/8 | 6/8 | **8/8** | 100% | 8/8 |
| check_inventory | 2/4 | 4/8 | 4/8 | **8/8** | 100% | 8/8 |
| lookup_order | 4/4 | 8/8 | 8/8 | **8/8** | 100% | 8/8 |
| get_shipping_status | 4/4 | 6/8 | 6/8 | **7/8** | 94% | 8/8 |
| search_orders | 4/4 | 8/8 | 8/8 | **8/8** | 100% | 8/8 |
| initiate_return | 4/4 | 8/8 | 8/8 | **8/8** | 100% | 8/8 |
| **Total** | **25/32 (78%)** | **54/64 (84%)** | **54/64 (84%)** | **61/64 (95%)** | 97% | 56/64 |

- **Consistency across paraphrases:** in V7, every paraphrase of 7 of the 8 benchmarks produced the expected answer, apart from one shipping reply that left out the carrier.
- **search_products:** the 2 misses are the shortened yoga names. The answers list the right products. Tool hit is 0/8 because these questions are now answered by `list_categories`, which returns the same products.

**Regression check on the 35-query eval set** (2 runs each, key facts):

| Category | V2 | V5 | V6 | **V7** |
|---|---|---|---|---|
| order_lookup | 32/32 | 32/32 | 32/32 | 32/32 |
| order_details | 29/32 | 31/32 | 32/32 | 32/32 |
| order_status | 4/6 | 3/6 | 4/6 | 3/6 |
| shipping | 10/10 | 8/10 | 9/10 | 10/10 |
| product_info | 7/8 | 8/8 | 6/8 | 8/8 |
| returns | 2/6 | 2/6 | 2/6 | 2/6 |
| inventory | 5/34 | 3/34 | 10/34 | 10/34 |
| product_search | 0/28 | 5/28 | 9/28 | **17/28** |
| **Total** | **89/156 (57%)** | **92/156 (59%)** | **104/156 (67%)** | **114/156 (73%)** |
| Empty replies | 1/70 | 0/70 | 0/70 | 0/70 |

- **V7 vs V2: +25 facts.** This is far larger than the 1-fact spread seen between repeated runs. Most of the gain is in product_search (0 → 17) and inventory (5 → 10), the two categories the earlier prompt versions could not fix.
- **Remaining inventory misses** are mostly query 5 ("fitness equipment… what's in stock", 11 facts). It expects stock counts for a whole category, and `list_categories` returns prices but not counts.
- `store.db` was unchanged after every run (same checksum).

### 4.8 Open issues

- **Overview questions with no argument:** in the V5 probe, about 6 of 15 overview questions called `list_categories` with no argument. The call failed validation, and the reply blamed "an issue". V7 passed 8/8 in the tool eval, but this was not probed again, so treat it as open. A possible fix is to split the tool into `list_categories()` and `list_products_in_category(category)`, so neither call has an optional argument. Not tested.
- **Shortened product names:** the model sometimes shortens names ("Yoga Leggings" for "High-Waist Yoga Leggings"). A prompt rule to copy names exactly might help. Not tested.
- **Category stock counts:** "what's in stock in X?" questions need counts per product, which `list_categories` does not return.
- **Order status (3/6) and returns (2/6)** did not change across V2–V7. Neither was investigated here.
- **Shipping carrier:** V5 and V6 each had 2 of 8 shipping replies without the carrier, and V7 had 1. The 35-query shipping score returned to 10/10 in V7, so this looks like noise. It is not explained.

---

## 5. Experiment: can the prompt teach the model to chain tools?

### 5.1 The question

Section 4.6 fixed the product questions by changing the tools. A fair question is: why not keep the original tools and use the prompt instead? A few-shot prompt could teach the model to break the question into steps: first find the product's ID, then use it. This section tests that idea.

**What "tool chaining" means here.** On the main branch, `get_product_details` and `check_inventory` only accept a numeric product ID. Customers give names. So a correct answer needs two calls, where the second call uses a number taken from the first call's result:

```
Customer:  How many Kettlebell 25lb Cast Iron do you have in stock?
Call 1:    search_products(query="kettlebell")
Result 1:  #93: Kettlebell 25lb Cast Iron (Fitness) — $49.99
Call 2:    check_inventory(product_id=93)        <- 93 comes from Result 1
Result 2:  Quantity available: 60
Reply:     We have 60 in stock.
```

### 5.2 On the main branch, as is

**Setup:** the original prompt and the original 7 tools (no `list_categories`), with `qwen2.5:3b`. Each question was asked 3 times.

| Question | Correct answer | What the agent did (3 runs) |
|---|---|---|
| "How many Kettlebell 25lb Cast Iron do you have in stock?" | 60 units (#93) | Empty reply, no tool call, 3/3 |
| "How much does the Vacuum Insulated Tumbler cost?" | $24.99 (#120) | Guessed `product_id=12345` once and `product_id=123` twice. ID 123 is the Insulated Cooler Bag, so one reply said the tumbler "is a Insulated Cooler Bag 24-Can… costs $39.99". |
| "Is the Yoga Mat Premium in stock?" | Yes, 75 units (#11) | Guessed `12345` twice and `123` once. The `123` reply said the yoga mat "is not in stock… We currently have 80 Insulated Cooler Bags". |
| "How many Portable Phone Chargers do you have left in stock?" | 200 units (#20) | Guessed `123` and `789`, then asked the customer for the product ID. |

- **Result:** 0 of 12 runs called `search_products` first, and 0 of 12 gave the right answer. When it called a tool, the model invented an ID.

**Run it yourself** on the main branch (Ollama running and `store.db` seeded). The snippet prints the tool calls, so you can see the guessed IDs:

```bash
poetry run python - <<'EOF'
from langchain_core.messages import HumanMessage
from src.agent import Agent

agent = Agent()
questions = [
    "How many Kettlebell 25lb Cast Iron do you have in stock?",
    "How much does the Vacuum Insulated Tumbler cost?",
    "Is the Yoga Mat Premium in stock?",
    "How many Portable Phone Chargers do you have left in stock?",
]
for q in questions:
    msgs = agent.graph.invoke({"messages": [HumanMessage(content=q)]})["messages"]
    calls = [(c["name"], c["args"]) for m in msgs for c in (getattr(m, "tool_calls", None) or [])]
    print(q)
    print("  tool calls:", calls)
    print("  reply:", msgs[-1].content[:200], "\n")
EOF
```

The model is not deterministic, so exact IDs vary between runs. What should not change is the pattern: no `search_products` call before the ID tool. The same questions in `poetry run chat` show the replies without the tool calls. On the current branch, the same snippet gives the right answers (for example, `check_inventory({'product': 'Kettlebell 25lb Cast Iron'})` → "We have 60…").

### 5.3 Can a better prompt fix it?

**Setup:** the original integer-ID product tools, with two prompt versions. Everything else (the other tools, including the V6 `list_categories`, and the rest of the prompt) is as in V6. The questions were the two name-based entries from the tool eval: the tumbler price (entry 6) and the Kettlebell stock (entry 8). Each had 4 paraphrases × 3 runs, so 24 runs per prompt.

- **P0, the current prompt style:** rule 4 ("If the customer names a product, call search_products first to get its ID") plus two-step examples, such as `search_products(query="hiking boot"), then check_inventory(product_id=<id from the search result>)`.
- **P1, explicit step-by-step breakdown:** P0's product entries replaced with:
  - "break the question into two steps";
  - what a search result line looks like (`#<id>: <name> (<category>) — <price>`);
  - two worked examples that take the `#id` from a sample search result and pass it on;
  - the rule "If the question has a product name but no number, your first call must be search_products."
  - One worked example used a made-up result line, which does not match the store's data.

| Setup | Correct answers | Searched, then used the ID |
|---|---|---|
| P0: rule plus two-step examples | 9/24 | **0/24** |
| P1: step-by-step breakdown with worked examples | 12/24 | **2/24** |
| Current tools (accept a name), from section 4.6 | 24/24 (48/48 incl. ID questions) | not needed |

**What the model did instead of chaining:**
- **Invented an ID:** `product_id=123`, `12345`, `789`, `45`, `15`, `78`.
- **Took a number from the product name:** "Kettlebell **25**lb" became `check_inventory(product_id=25)`. ID 25 is the Waterproof Rain Boots, which has 65 units. That is where the "65 Kettlebells" answers in sections 4.6 and 4.8 came from.
- **Put the name in the ID field:** `get_product_details(product_id="Vacuum Insulated Tumbler")`, which fails validation ("issue parsing the product ID").
- **Stopped after the search:** under P1, most tumbler questions called `search_products` first, which is progress. But the model then answered from that result and never made the second call. The tumbler answers were still right, because the search result already shows the price. The stock questions were wrong in all 12 runs under both prompts, because the search result has no stock count.

### 5.4 Conclusion

- **This model does not chain tools reliably.** Across 5 prompt versions (the original prompt, V2, V3, P0 and P1), it almost never read an ID from one tool's result and passed it to a second tool: 2 times in 60 runs here.
- **Few-shot examples change the first call, not the second.** P1 made the model start with `search_products` more often. It did not make it continue to the second, dependent call.
- **So the tools were changed to need only one call.** When the product tools accept a name, the same questions pass 48/48. Shaping tools to fit the model is a normal design choice, and the challenge fixes the model.
- **Limits of this test:** only 3 runs per question, and only two prompt styles in this experiment. A larger model would likely chain, but that was not tested, since the challenge fixes the model.

---

## 6. Final artifacts

**`src/agent/tools.py`**
- **`list_categories(category: str)`:**
  - With `"all"`, it lists in-stock categories with counts and price ranges.
  - With a category, kind of product or phrase ("books", "yoga gear"), it matches on keywords and lists the matching category's in-stock products.
  - If no category matches, it falls back to in-stock products whose names contain a keyword, and then to the full category list.
- **`get_product_details(product: str)` and `check_inventory(product: str)`:** each accepts an ID ("33", "#33") or a name. A name resolves to an exact match, or else the closest name matches. One call is enough; the model no longer has to search for the ID first.
- The other tools are unchanged. All tools are registered in `ALL_TOOLS`, so `graph.py` needed no changes.

**`eval/run_tool_eval.py` and `eval/test_tool_queries.json`:** the tool-call eval (section 4.1).

**`src/agent/prompts.py`: final system prompt (V7 = V2 with the catalog entry from section 4.5 and the product entries and rule 4 from section 4.6)**
1. **Role:** one sentence (ShopEasy support; orders, products, shipping, returns; friendly and concise).
2. **4 rules:**
   1. Call only the listed tools, by their exact names. The list is built from `ALL_TOOLS`.
   2. Get facts only from tools.
   3. Answer only from what the tools return, and suggest a next step if nothing is found.
   4. Never guess an ID; pass the product name instead.
3. **"Which tool to call":** 9 short entries. Each has a heading and example questions mapped to exact calls, plus a short note where needed (for example, ask for the email if it's missing).

**Design choices and the evidence behind them:**

| Choice | Why |
|---|---|
| One-line question → call mappings, not full dialogues | In our tests, full dialogues led to invented tool names (plain-text format) or a copied example reply (native format). See Step 6. |
| An explicit exact-name rule | It removed the empty replies caused by invented tool names in the real-endpoint probe (Step 7). |
| An entry for every tool | It scored highest on the eval set: 57%, against 44% for V1 with catalog entries only. Rule 4 was added at the same time, so the gain can't be credited to the entries alone (Step 8). |
| No sample tool output (prices, counts, lists) in the examples | When the examples contained a sample reply, the model repeated it instead of calling the tool (Step 6). |
| Examples don't reuse eval query wording, order numbers or emails | Keeps the eval score honest. |
| `list_categories` takes a required `category`, with `"all"` for the overview | With an optional argument, the model left it out on "which books…" questions and answered with only the summary (0/12 and 4/12). Required: 12/12 (section 4.4). |
| Tools match on keywords and fall back instead of returning nothing | The model passes the customer's own words ("books", "yoga gear", "departments"). A fallback still gives it something useful to answer from (sections 4.5 and 4.6). |
| Product tools accept a name as well as an ID | The model would not search for an ID before using it under any prompt wording (Step 9, section 5). Accepting a name made those questions single-call: 48/48 in the probe, and inventory/product_search rose from 5 + 0 to 10 + 17 facts (section 4.6). |

---

## 7. How results were measured

- **Spot checks:** real questions through the full agent (`Agent().graph.invoke`), recording the tool-call sequence as well as the reply. A reply that looked right but called no tool (such as the copied example reply in Step 6) was counted as a failure.
- **Tool-choice probes:** 5–6 samples per question, recording the first tool call. The early probes (Step 6) used a hand-built copy of the chat template. After Step 7 showed that this could disagree with the real endpoint, probes went through Ollama's `/api/chat` with the real tool schemas. There, "empty" means a reply with neither text nor a tool call.
- **Eval set:** all 35 queries in `eval/test_queries.json`, 2 runs per prompt.
  - **Score:** the share of key facts from each `expected_answer` that appear in the reply. Key facts are dollar amounts, tracking numbers like `UPS-1002-2026`, and stock counts. A stock count counts as found if the number appears anywhere in the reply.
  - **Isolation:** each run copies `store.db` to a scratch file first, because `initiate_return` inserts rows. The real `store.db` still has its original 11 returns.

**Limitations to keep in mind:**
- **The metric is crude.** It checks for facts, not the correctness of the whole reply. It doesn't penalize wrong or invented facts, such as another product's stock reported as the asked-for product's. Expected answers with no numbers add nothing to the score. The stock-count check is lenient, since any matching number in the reply counts.
- **Categories are weighted unevenly.** Query 5 alone has 11 facts and query 24 has 8, so inventory and product_search dominate the total.
- **The sample is small.** Two separate 2-run evals of the same V3 prompt scored 85 and 86, so differences of a few facts are noise. The V2 lead over the original (+13 facts) and the order_lookup gain (+12) are larger than that, but only one noise estimate exists, so treat them as likely gains, not proven ones.
- **The baseline already includes the new tool.** The "Original" row is the original prompt with `list_categories` available, so it isolates the prompt change, not the tool change.
- **The 35-query scoring script is not in the repo yet.** It was written in a scratch directory during the session. The tool-call eval is in the repo (`eval/run_tool_eval.py`).

---

## 8. Lessons for prompting a 3B tool-calling model

These are what this model showed in these tests, not general rules.

1. **Test questions outside the area you're changing.** The worst regression (empty order replies) came from a change made for catalog questions.
2. **Full examples can backfire.** In these tests, a sample reply in the prompt was copied word for word, and full examples were linked to invented tool names. Question → call mappings with no sample output avoided both.
3. **Name the tools explicitly.** Without the exact list, the model sometimes invented plausible names (`get_order_status`), which showed up as empty replies.
4. **Cover all the tools.** The prompt with an entry for every tool scored best (57%, against 44% for catalog entries only).
5. **Test through the real serving path.** A hand-built template gave different results from Ollama's real endpoint.
6. **Notice when wording stops helping.** The search-then-look-up chain did not improve with any of the wordings tried. Changing the tools so that one call is enough fixed it (V7: 48/48 in the probe).
7. **The tool schema matters as much as the prompt.** The model left out an optional argument even when the prompt showed it being passed, and a required argument fixed that. The prompt rule "always pass a category" made things worse (section 4.4).
8. **Test the same question in several wordings, and read the replies by hand.** One wording can pass while another fails. "tell me what all books…" worked, but "What books do you have?" did not. A paraphrase set catches this; a single test query doesn't. Manual sessions also found failures ("yoga gear", the guessed tumbler ID) that a pass rate alone made look minor.

---

## 9. Next steps, in priority order

1. **Finish the single-call tool work.** The main part is done: the product tools accept names (V7) and `list_categories` matches on keywords (V6). Remaining:
   - **Split `list_categories` into two tools with no optional argument** (`list_categories()` and `list_products_in_category(category)`), to fix the overview questions that fail validation (section 4.8).
   - **Add stock counts to category listings**, for "what's in stock in X?" questions (query 5).
   - **Add synonyms** ("skincare" → Beauty, "camping" → Outdoor), or search product descriptions.
   - **Look into order status and returns**, which have not moved since V2.
2. **Build a proper eval harness in the repo.** The tool-call eval (`eval/run_tool_eval.py`) is a first step: it lives in the repo, isolates the DB, and reports whether the expected tool was called. Still to do: promote the 35-query fact scorer from the scratch directory to `eval/`, and add:
   - an expected tool-call sequence for each query that fails the run when the tools don't match (the tool eval reports a tool hit but doesn't fail on it);
   - a check for invented facts (numbers in the reply that no tool returned);
   - at least 3 runs per prompt, reported with spread.

   The tool eval now covers "what categories do you sell?" and "what do you have in X?". Still to add: "what are the best X?" (should decline, since there are no ratings), and casual phrasings. The challenge allows adding cases.
3. **Rewrite the tool docstrings.** Several are vague ("Handle a customer issue with an order. Use this when a customer has a problem." for `initiate_return`; "Get information about an item." for `get_product_details`). LangChain passes these docstrings to the model as the tool descriptions, so clearer ones may help tool choice without making the prompt longer. This was not tested here; measure it with the harness from step 2.
