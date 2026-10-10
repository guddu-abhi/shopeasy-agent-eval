"""Ground-truth DB records for each query, for the "Factual DB records" and "DB query" columns of labels.csv.

labels.py adds these columns when it writes labels.csv. To print the facts for some queries:
    python db_facts.py [store.db] [id ...]
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parents[2] / "store.db"
COLUMNS = ("Factual DB records", "DB query")

ORDERS_BY_EMAIL = ("SELECT c.id AS customer_id, c.name, o.id AS order_id, o.status, o.created_at, o.total "
                   "FROM orders o JOIN customers c ON o.customer_id = c.id "
                   "WHERE c.email = '{}' ORDER BY o.created_at DESC;")
SHIPPING = ("SELECT o.id AS order_id, o.status AS order_status, s.carrier, s.tracking_number, "
            "s.status AS shipping_status, s.estimated_delivery, s.shipped_at "
            "FROM orders o LEFT JOIN shipping s ON s.order_id = o.id WHERE o.id = {};")
ORDER_ITEMS = ("SELECT o.id AS order_id, o.status, o.created_at, o.total, i.product_name, i.quantity, i.unit_price "
               "FROM orders o LEFT JOIN order_items i ON i.order_id = o.id WHERE o.id = {};")
ORDER_FULL = ("SELECT o.id AS order_id, o.status, o.created_at, o.total, i.product_name, i.quantity, i.unit_price, "
              "s.carrier, s.tracking_number, s.status AS shipping_status, s.estimated_delivery "
              "FROM orders o LEFT JOIN order_items i ON i.order_id = o.id "
              "LEFT JOIN shipping s ON s.order_id = o.id WHERE o.id = {};")
ORDER_RETURNS = ("SELECT o.id AS order_id, o.status, o.created_at, o.total, i.product_name, "
                 "r.id AS return_id, r.reason AS return_reason, r.status AS return_status, r.refund_amount "
                 "FROM orders o LEFT JOIN order_items i ON i.order_id = o.id "
                 "LEFT JOIN returns r ON r.order_id = o.id WHERE o.id = {};")
PRODUCT_BY_NAME = ("SELECT id, name, category, price, stock_quantity FROM products "
                   "WHERE name LIKE '%{}%' ORDER BY id;")
CATEGORY = ("SELECT id, name, price, stock_quantity FROM products "
            "WHERE category = '{}' ORDER BY id;")

# query id -> (SQL, note). The note adds context the rows alone do not show; it may be empty.
FACTS = {
    1: (PRODUCT_BY_NAME.format("Ultraboost"), ""),
    2: (ORDERS_BY_EMAIL.format("alice@example.com"), ""),
    3: (SHIPPING.format(2), ""),
    4: (ORDER_RETURNS.format(14), "No return exists yet, so initiate_return should create one."),
    5: (CATEGORY.format("Fitness"), "No product name or category contains 'fitness equipment'; the category is 'Fitness'."),
    6: (SHIPPING.format(11), ""),
    7: (ORDERS_BY_EMAIL.format("bob@example.com"), ""),
    8: (PRODUCT_BY_NAME.format("Portable Phone Charger"), ""),
    9: (ORDER_FULL.format(7), ""),
    10: (PRODUCT_BY_NAME.format("Leather Messenger Bag"), ""),
    11: ("SELECT id, name, category, price, description FROM products WHERE name LIKE '%Yoga Mat Premium%';", ""),
    12: (SHIPPING.format(25), ""),
    13: (ORDER_ITEMS.format(8), "created_at is the date the order was placed."),
    14: (ORDER_ITEMS.format(10), ""),
    15: (ORDER_ITEMS.format(17), ""),
    16: (PRODUCT_BY_NAME.format("sunglass"), ""),
    17: ("SELECT id, name, category, price FROM products WHERE id = 4;", ""),
    18: (ORDER_RETURNS.format(12), "A return already exists for this order."),
    19: (SHIPPING.format(74), ""),
    20: (ORDERS_BY_EMAIL.format("bianca@example.com"), ""),
    21: (PRODUCT_BY_NAME.format("Robot Vacuum"), ""),
    22: ("SELECT id, name, category, price, description FROM products "
         "WHERE category = 'Books' AND (name LIKE '%cook%' OR description LIKE '%cook%' OR description LIKE '%recipe%') ORDER BY id;",
         "Category is 'Books'; 'Python Programming Cookbook' also matches 'cook' but is not about cooking."),
    23: (ORDER_RETURNS.format(64), "A return already exists for this order."),
    24: (CATEGORY.format("Outdoor"), ""),
    25: (ORDER_ITEMS.format(40), ""),
    26: (SHIPPING.format(58), ""),
    27: (CATEGORY.format("Beauty"), "No product name or category contains 'skincare'; these products are in 'Beauty'."),
    28: (PRODUCT_BY_NAME.format("Massage Gun"), ""),
    29: (SHIPPING.format(41), ""),
    30: (ORDERS_BY_EMAIL.format("diana@example.com"), ""),
    31: (ORDER_RETURNS.format(46), "A return already exists for this order."),
    32: (PRODUCT_BY_NAME.format("Hammock"), ""),
    33: (ORDER_ITEMS.format(70), ""),
    34: (ORDERS_BY_EMAIL.format("sam@example.com"), ""),
    35: ("SELECT id, name, category, price, description FROM products WHERE name LIKE '%Python Programming Cookbook%';", ""),
    "S1": ("SELECT id, status, total FROM orders WHERE id = 999;", "Order #999 does not exist."),
    "S2": (ORDER_RETURNS.format(3), "Order is pending, so initiate_return refuses it."),
    "S3": (ORDER_RETURNS.format(47), "Order is cancelled, so initiate_return refuses it."),
    "S4": (ORDERS_BY_EMAIL.format("nobody@example.com"), "No customer has this email."),
    "S5": (PRODUCT_BY_NAME.format("laptop"), "No laptops are sold; the only match is an accessory."),
    "S6": ("", "No order number or email given, so there is nothing to look up."),
    "S7": (SHIPPING.format(5).replace("o.status AS order_status,", "o.status AS order_status, o.total,"), ""),
    "S8": (PRODUCT_BY_NAME.format("Wireless Ergonomic Mouse"), ""),
    "S9": ("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name;",
           "The DB has no policy table; these are all the tables."),
    "S10": (SHIPPING.format(72), "Order is pending and has no shipping row."),
    "S11": ("SELECT o.id AS order_id, o.status, o.created_at, s.status AS shipping_status, s.estimated_delivery "
            "FROM orders o JOIN customers c ON o.customer_id = c.id LEFT JOIN shipping s ON s.order_id = o.id "
            "WHERE c.email = 'alice@example.com' ORDER BY o.created_at DESC;", "Not yet arrived: orders not 'delivered'."),
    "S12": ("SELECT c.email, o.id AS order_id, o.status, o.total FROM orders o JOIN customers c ON o.customer_id = c.id "
            "WHERE c.email = 'Alice@Example.com' COLLATE NOCASE ORDER BY o.created_at DESC;",
            "The tool's exact match (c.email = 'Alice@Example.com') returns 0 rows; ignoring case returns these."),
}


class RowSummarizer:
    """Turns query rows into one line: columns that are the same in every row are printed once."""

    def __init__(self, max_rows: int = 6):
        self.max_rows = max_rows  # longer results are cut in the summary; the SQL returns all rows

    def summarize(self, rows: list[sqlite3.Row]) -> str:
        if not rows:
            return "0 rows."
        cols = list(rows[0].keys())
        const = [c for c in cols if len(rows) > 1 and len({r[c] for r in rows}) == 1]
        vary = [c for c in cols if c not in const]
        parts = [f"{len(rows)} row{'s' if len(rows) > 1 else ''}."]
        if const:
            parts.append("All rows: " + ", ".join(f"{c}={self._fmt(rows[0][c])}" for c in const) + ".")
        parts.append(" | ".join(", ".join(f"{c}={self._fmt(r[c])}" for c in vary) for r in rows[:self.max_rows]))
        if len(rows) > self.max_rows:
            parts.append(f"(+{len(rows) - self.max_rows} more rows; run the query for all)")
        return " ".join(parts)

    @staticmethod
    def _fmt(v) -> str:
        return "NULL" if v is None else str(v)


class DbFacts:
    """Runs each query's SQL read-only on store.db and returns (summary, sql) per query id."""

    def __init__(self, db_path: str | Path = DEFAULT_DB, facts: dict = FACTS, summarizer: RowSummarizer | None = None):
        self.db_path = Path(db_path)
        self.facts = {str(k): v for k, v in facts.items()}  # ids are ints or "S1"-style strings
        self.summarizer = summarizer or RowSummarizer()
        self._cache: dict[str, tuple[str, str]] = {}

    def for_query(self, qid) -> tuple[str, str]:
        key = str(qid)
        if key not in self._cache:
            self._cache[key] = self._compute(key)
        return self._cache[key]

    def _compute(self, key: str) -> tuple[str, str]:
        sql, note = self.facts[key]
        text = ""
        if sql:
            with sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True) as conn:
                conn.row_factory = sqlite3.Row
                text = self.summarizer.summarize(conn.execute(sql).fetchall())
        return " ".join(p for p in (note, text) if p), sql


def main():
    args = sys.argv[1:]
    db = args.pop(0) if args and args[0].endswith(".db") else DEFAULT_DB
    facts = DbFacts(db)
    for qid in args or FACTS:
        text, sql = facts.for_query(qid)
        print(f"[{qid}] {text}\n    {sql}\n")


if __name__ == "__main__":
    main()
