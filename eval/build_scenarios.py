"""Build the held-out scenario set (test_scenarios.json) from store.db.

Each scenario is one tuple of four dimensions, chosen from failures seen in
the other evals:

- intent:     what the customer wants (inventory, product_info, order_details,
              shipping, order_status, order_lookup, returns, out_of_scope)
- ref:        how they name the entity (id, exact_name, partial_name, email,
              none, nonexistent)
- state:      the data behind it (normal, not_shipped, pending, shipped,
              delivered, return_exists, not_sold, not_found)
- phrasing:   formal or casual

Expected checks come from SQL, not from hand-written answers. Entities used in
test_queries.json, test_tool_queries.json or the prompt's examples are
excluded, so this set stays unseen while tuning. Do not tune on it.

Usage:
    python -m eval.build_scenarios            # writes eval/test_scenarios.json
"""

from __future__ import annotations

import json
import random
import re
import sqlite3
from pathlib import Path

from src.data.database import DB_PATH

EVAL_DIR = Path(__file__).resolve().parent
OUT = EVAL_DIR / "test_scenarios.json"

# Replies that decline or say something does not exist contain one of these.
NEGATIVE = ["not", "no ", "don't", "do not", "doesn't", "couldn't", "unable", "sorry", "can't", "cannot"]

TEMPLATES = {
    ("inventory", "formal"): "Could you tell me whether the {name} is in stock, and how many are available?",
    ("inventory", "casual"): "hey do u have any {name} left? how many",
    ("product_info", "formal"): "What is the price of product #{id}?",
    ("product_info", "casual"): "how much is item {id}",
    ("order_details", "formal"): "Could you tell me what was in order #{id} and what it cost in total?",
    ("order_details", "casual"): "whats in order {id} and how much did i pay",
    ("shipping", "formal"): "Could you give me the tracking number and carrier for order #{id}?",
    ("shipping", "casual"): "where's my package for order {id}?? tracking pls",
    ("order_status", "formal"): "What is the current status of order #{id}?",
    ("order_status", "casual"): "any update on order {id}",
    ("order_lookup", "formal"): "Please list all orders for {email}.",
    ("order_lookup", "casual"): "can u pull up my orders? email is {email}",
    ("returns", "formal"): "I would like to return order #{id} because {reason}.",
    ("returns", "casual"): "need to send back order {id}, {reason}",
}

# Not sold (checked in SQL only). Kept apart from the names probed while fixing
# product matching, so this slice stays unseen.
UNSOLD = ["Electric Scooter", "Snowboard Bindings", "Camping Tent 4-Person", "Acoustic Guitar"]
REASONS = ["it arrived damaged", "it doesn't fit", "I ordered the wrong size", "it stopped working"]


def used_entities() -> tuple[set[int], set[str], set[str]]:
    texts = []
    for e in json.loads((EVAL_DIR / "test_queries.json").read_text()):
        texts += [e["query"], e["expected_answer"]]
    for e in json.loads((EVAL_DIR / "test_tool_queries.json").read_text()):
        texts += e["questions"] + [e["expected_answer"]]
    texts.append((EVAL_DIR.parent / "src" / "agent" / "prompts.py").read_text())
    blob = "\n".join(texts)
    orders = {int(x) for x in re.findall(r"(?:#|order )(\d+)", blob, re.IGNORECASE)}
    emails = set(re.findall(r"[\w.]+@example\.com", blob))
    return orders, emails, blob.lower()


def money(x: float) -> str:
    return f"${x:.2f}"


def build(seed: int = 0) -> list[dict]:
    rng = random.Random(seed)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    used_orders, used_emails, used_text = used_entities()

    def pick(rows, k):
        rows = list(rows)
        return rng.sample(rows, min(k, len(rows)))

    products = [p for p in conn.execute("SELECT * FROM products") if p["name"].lower() not in used_text]
    orders = [o for o in conn.execute(
        "SELECT o.*, c.email, s.tracking_number, s.carrier, r.id AS return_id, "
        "r.reason AS return_reason, r.refund_amount "
        "FROM orders o JOIN customers c ON c.id = o.customer_id "
        "LEFT JOIN shipping s ON s.order_id = o.id LEFT JOIN returns r ON r.order_id = o.id"
    ) if o["id"] not in used_orders]

    scenarios: list[dict] = []

    def add(intent, ref, state, phrasing, query, must=(), any_of=(), returns_after=None):
        scenarios.append({
            "id": len(scenarios) + 1,
            "intent": intent, "ref": ref, "state": state, "phrasing": phrasing,
            "query": query,
            "must_contain": list(must),
            "must_contain_any": list(any_of),
            **({"returns_after": returns_after} if returns_after else {}),
        })

    phrasings = ["formal", "casual"]

    # Inventory: exact name, partial name (first two words), and unsold products.
    for i, p in enumerate(pick(products, 4)):
        ph = phrasings[i % 2]
        add("inventory", "exact_name", "normal", ph,
            TEMPLATES[("inventory", ph)].format(name=p["name"]), must=[str(p["stock_quantity"])])
    for i, p in enumerate(pick([p for p in products if len(p["name"].split()) >= 3], 3)):
        ph = phrasings[i % 2]
        short = " ".join(p["name"].split()[:2])
        # The stock count shows the right product was found; the reply may
        # reuse the customer's shorter name.
        add("inventory", "partial_name", "normal", ph,
            TEMPLATES[("inventory", ph)].format(name=short), must=[str(p["stock_quantity"])])
    for i, name in enumerate(UNSOLD):
        ph = phrasings[i % 2]
        add("inventory", "nonexistent", "not_sold", ph,
            TEMPLATES[("inventory", ph)].format(name=name), any_of=NEGATIVE)

    # Product info by ID, plus an ID that does not exist.
    for i, p in enumerate(pick(products, 3)):
        ph = phrasings[i % 2]
        add("product_info", "id", "normal", ph,
            TEMPLATES[("product_info", ph)].format(id=p["id"]), must=[money(p["price"]), p["name"]])
    add("product_info", "nonexistent", "not_found", "formal",
        TEMPLATES[("product_info", "formal")].format(id=999), any_of=NEGATIVE)

    # Order details, and an order that does not exist.
    for i, o in enumerate(pick(orders, 4)):
        ph = phrasings[i % 2]
        add("order_details", "id", "normal", ph,
            TEMPLATES[("order_details", ph)].format(id=o["id"]), must=[money(o["total"])])
    add("order_details", "nonexistent", "not_found", "casual",
        TEMPLATES[("order_details", "casual")].format(id=500), any_of=NEGATIVE)

    # Shipping: shipped orders, and pending orders with no shipment yet.
    shipped = [o for o in orders if o["tracking_number"]]
    for i, o in enumerate(pick(shipped, 4)):
        ph = phrasings[i % 2]
        # The casual wording asks only for tracking, not the carrier.
        must = [o["tracking_number"], o["carrier"]] if ph == "formal" else [o["tracking_number"]]
        add("shipping", "id", "normal", ph,
            TEMPLATES[("shipping", ph)].format(id=o["id"]), must=must)
    for i, o in enumerate(pick([o for o in orders if o["status"] == "pending"], 2)):
        ph = phrasings[i % 2]
        add("shipping", "id", "not_shipped", ph,
            TEMPLATES[("shipping", ph)].format(id=o["id"]), any_of=NEGATIVE + ["pending", "yet"])

    # Order status across states.
    for i, status in enumerate(["pending", "shipped", "delivered", "cancelled"]):
        candidates = [o for o in orders if o["status"] == status]
        if candidates:
            o = rng.choice(candidates)
            ph = phrasings[i % 2]
            add("order_status", "id", status, ph,
                TEMPLATES[("order_status", ph)].format(id=o["id"]), must=[status])

    # Order lookup by email, a missing email, and an unknown email.
    by_email: dict[str, list] = {}
    for o in conn.execute("SELECT o.total, c.email FROM orders o JOIN customers c ON c.id = o.customer_id"):
        by_email.setdefault(o["email"], []).append(money(o["total"]))
    emails = [e for e in by_email if e not in used_emails]
    for i, email in enumerate(pick(emails, 3)):
        ph = phrasings[i % 2]
        add("order_lookup", "email", "normal", ph,
            TEMPLATES[("order_lookup", ph)].format(email=email), must=by_email[email])
    add("order_lookup", "none", "normal", "casual", "can you show me all my orders?", any_of=["email"])
    add("order_lookup", "nonexistent", "not_found", "formal",
        TEMPLATES[("order_lookup", "formal")].format(email="nobody@example.com"), any_of=NEGATIVE)

    # Returns: eligible, not yet shipped, already returned.
    eligible = [o for o in orders if o["status"] == "delivered" and not o["return_id"]]
    for i, o in enumerate(pick(eligible, 3)):
        ph = phrasings[i % 2]
        add("returns", "id", "normal", ph,
            TEMPLATES[("returns", ph)].format(id=o["id"], reason=rng.choice(REASONS)),
            must=[money(o["total"])], returns_after={str(o["id"]): 1})
    for i, o in enumerate(pick([o for o in orders if o["status"] == "pending"], 2)):
        ph = phrasings[i % 2]
        add("returns", "id", "pending", ph,
            TEMPLATES[("returns", ph)].format(id=o["id"], reason=rng.choice(REASONS)),
            any_of=NEGATIVE, returns_after={str(o["id"]): 0})
    for i, o in enumerate(pick([o for o in orders if o["return_id"]], 2)):
        ph = phrasings[i % 2]
        add("returns", "id", "return_exists", ph,
            TEMPLATES[("returns", ph)].format(id=o["id"], reason=rng.choice(REASONS)),
            must=["already"], returns_after={str(o["id"]): 1})

    # Out of scope: the data has no ratings or reviews.
    add("out_of_scope", "none", "normal", "formal",
        "Which of your headphones has the best customer reviews?", any_of=NEGATIVE + ["review", "rating"])
    add("out_of_scope", "none", "normal", "casual",
        "whats ur top rated running shoe", any_of=NEGATIVE + ["review", "rating"])

    conn.close()
    return scenarios


def main() -> None:
    scenarios = build()
    OUT.write_text(json.dumps(scenarios, indent=2) + "\n")
    print(f"Wrote {len(scenarios)} scenarios to {OUT}")


if __name__ == "__main__":
    main()
