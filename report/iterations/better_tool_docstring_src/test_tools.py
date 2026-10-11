"""Deterministic tool tests. No LLM is called, so these run in seconds in CI.

Every test runs against a fresh copy of store.db, because initiate_return
writes rows.

Usage:
    python -m unittest discover tests
"""

from __future__ import annotations

import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

import src.data.database as database
from src.agent.tools import (
    check_inventory,
    get_product_details,
    initiate_return,
    list_categories,
    lookup_order,
)


def names(result: dict) -> list[str]:
    """The product names in a tool result."""
    return [p["name"] for p in result.get("products", [])]


class ToolTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._source = database.DB_PATH
        database.DB_PATH = Path(self._tmp.name) / "store.db"
        shutil.copy(self._source, database.DB_PATH)

    def tearDown(self):
        database.DB_PATH = self._source
        self._tmp.cleanup()

    def count_returns(self, order_id: int) -> int:
        conn = sqlite3.connect(database.DB_PATH)
        n = conn.execute("SELECT COUNT(*) FROM returns WHERE order_id = ?", (order_id,)).fetchone()[0]
        conn.close()
        return n


class ProductLookupTests(ToolTestCase):
    def test_exact_name(self):
        [product] = check_inventory.invoke({"product": "Kettlebell 25lb Cast Iron"})["products"]
        self.assertEqual(product["product_id"], 93)
        self.assertEqual(product["quantity_available"], 60)

    def test_id_formats(self):
        for ref in ["93", "#93", "product 93", "Product ID 93"]:
            with self.subTest(ref=ref):
                self.assertIn("Kettlebell 25lb Cast Iron", names(check_inventory.invoke({"product": ref})))

    def test_partial_name_finds_product(self):
        out = get_product_details.invoke({"product": "Vacuum Insulated Tumbler"})
        self.assertEqual(out["products"][0]["price"], "$24.99")
        self.assertIn("Blue Ultraboost Running Shoe", names(check_inventory.invoke({"product": "Blue Running Shoe"})))

    def test_unsold_product_returns_no_unrelated_matches(self):
        # Before whole-word matching, "air" matched "Hair Clip Set" and "pro"
        # matched "Portable Mini Projector".
        for ref, wrong in [("Nike Air Max", "Hair Clip"), ("iPhone 15 Pro", "Projector")]:
            with self.subTest(ref=ref):
                self.assertFalse(any(wrong in n for n in names(check_inventory.invoke({"product": ref}))))

    def test_close_match_is_labelled_not_exact(self):
        # The store sells a 25lb kettlebell, not a 50lb one. The tool must not
        # present the 25lb one as the product asked about.
        out = check_inventory.invoke({"product": "Kettlebell 50lb"})
        self.assertIn("No exact match", out["note"])
        self.assertIn("Kettlebell 25lb Cast Iron", names(out))


class CatalogTests(ToolTestCase):
    def test_overview_lists_ten_categories(self):
        out = list_categories.invoke({"category": "all"})
        self.assertEqual(
            [c["category"] for c in out["categories"]],
            ["Accessories", "Beauty", "Books", "Clothing", "Electronics",
             "Fitness", "Footwear", "Home", "Outdoor", "Toys & Games"],
        )

    def test_customer_words_find_category(self):
        self.assertEqual(len(list_categories.invoke({"category": "books"})["products"]), 12)

    def test_phrase_falls_back_to_product_names(self):
        out = names(list_categories.invoke({"category": "yoga gear"}))
        self.assertIn("Yoga Mat Premium", out)
        self.assertIn("High-Waist Yoga Leggings", out)


class OrderTests(ToolTestCase):
    def test_lookup_order(self):
        out = lookup_order.invoke({"order_id": 10})
        self.assertEqual(out["total"], "$84.95")

    def test_missing_order(self):
        self.assertIn("No order found", lookup_order.invoke({"order_id": 9999})["error"])


class ReturnTests(ToolTestCase):
    def test_new_return_creates_one_row(self):
        self.assertEqual(self.count_returns(14), 0)
        out = initiate_return.invoke({"order_id": 14, "reason": "speaker stopped working"})
        self.assertEqual(out["refund_amount"], "$79.99")
        self.assertEqual(self.count_returns(14), 1)
        # A second request must not create a duplicate.
        self.assertIn("already exists", initiate_return.invoke({"order_id": 14, "reason": "again"})["note"])
        self.assertEqual(self.count_returns(14), 1)

    def test_pending_order_cannot_be_returned(self):
        out = initiate_return.invoke({"order_id": 3, "reason": "changed my mind"})
        self.assertIn("Cannot process return", out["error"])
        self.assertEqual(self.count_returns(3), 0)

    def test_existing_return_reports_reason_and_refund(self):
        # Eval queries 18 and 31 expect the existing return's reason and refund.
        out = initiate_return.invoke({"order_id": 12, "reason": "wrong color"})
        self.assertIn("already exists", out["note"])
        self.assertEqual(out["reason"], "Sole separated after one hike")
        self.assertEqual(out["refund_amount"], "$149.99")


if __name__ == "__main__":
    unittest.main()
