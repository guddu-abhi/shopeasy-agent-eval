# ShopEasy Customer Support Agent

An e-commerce customer support agent built with LangGraph, Ollama, and a local SQLite store. This repo is intentionally small and serves as the starting point for an agentic evaluation technical test focused on measuring and improving agent quality.

## Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation) installed
- [Ollama](https://ollama.com/) installed and running

## Setup

```bash
# Install dependencies and the local package
poetry install

# Pull the default local model
ollama pull qwen2.5:3b

# Rebuild the local SQLite database from seed data
poetry run seed-db
```

The repo uses Poetry for dependency management and package installation.
`poetry install` creates the environment and installs the local project so the
`chat`, `seed-db`, and `run-eval` scripts are available through `poetry run`.

## Usage

### Interactive chat

```bash
poetry run python main.py
```

Or use the installed console script:

```bash
poetry run chat
```

Type your questions and `/quit` to exit.

### Programmatic usage

```python
from src.agent import Agent

agent = Agent()
response = agent.run("What items are in order #10?")
print(response)
```

### Run evaluation

```bash
poetry run python -m eval.run_eval
```

Or:

```bash
poetry run run-eval
```

This runs 35 fixed evaluation queries and prints expected vs actual answers side by side.

## Project Structure

```text
src/
  agent/
    __init__.py     # Agent wrapper with a simple run() interface
    graph.py        # LangGraph ReAct agent construction
    tools.py        # Tool definitions used by the agent
    prompts.py      # System prompt
  data/
    __init__.py
    database.py     # SQLite connection and schema
    models.py       # Dataclasses for store entities
    seed.py         # Mock data generation / seeding
eval/
  __init__.py
  run_eval.py       # Evaluation runner
  test_queries.json # Eval dataset
main.py             # CLI chat interface
INSTRUCTIONS.md     # Technical test brief
store.db            # Local SQLite database
```

## Data

The seeded database represents a fictional e-commerce store and currently contains:

- 30 customers
- 170 products across 10 categories
- 76 orders
- 188 order items
- 66 shipping records
- 11 return requests

The checked-in `store.db` reflects that seeded dataset, and `seed-db` can be used to recreate it locally.

## Agent Design

The runtime agent is currently minimal:

- `src.agent.graph.build_graph()` constructs a LangGraph ReAct agent via `create_react_agent(...)`
- `ChatOllama` is used as the LLM backend
- `src.agent.prompts.SYSTEM_PROMPT` is a short customer-support instruction prompt
- `src.agent.tools.ALL_TOOLS` exposes the toolset to the agent

## Tools

The agent currently has 7 SQLite-backed tools:

| Tool | Purpose |
|------|---------|
| `lookup_order` | Fetch order details by order ID |
| `search_orders` | Search orders by customer email |
| `get_product_details` | Get product info by product ID |
| `search_products` | Search the product catalog by keyword/category |
| `check_inventory` | Check stock level for a product |
| `get_shipping_status` | Get shipping and tracking info for an order |
| `initiate_return` | Create a return request when eligible |

## Technical Test Context

The core assignment is described in `INSTRUCTIONS.md`: define what performance should mean for this stage of the project, measure it, and improve it *without* changing the underlying LLM.
