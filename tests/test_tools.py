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
        out = check_inventory.invoke({"product": "Kettlebell 25lb Cast Iron"})
        self.assertIn("#93", out)
        self.assertIn("Quantity available: 60", out)

    def test_id_formats(self):
        for ref in ["93", "#93", "product 93", "Product ID 93"]:
            with self.subTest(ref=ref):
                self.assertIn("Kettlebell 25lb Cast Iron", check_inventory.invoke({"product": ref}))

    def test_partial_name_finds_product(self):
        out = get_product_details.invoke({"product": "Vacuum Insulated Tumbler"})
        self.assertIn("$24.99", out)
        self.assertIn("Blue Ultraboost Running Shoe", check_inventory.invoke({"product": "Blue Running Shoe"}))

    def test_unsold_product_returns_no_unrelated_matches(self):
        # Before whole-word matching, "air" matched "Hair Clip Set" and "pro"
        # matched "Portable Mini Projector".
        for ref, wrong in [("Nike Air Max", "Hair Clip"), ("iPhone 15 Pro", "Projector")]:
            with self.subTest(ref=ref):
                self.assertNotIn(wrong, check_inventory.invoke({"product": ref}))

    def test_close_match_is_labelled_not_exact(self):
        # The store sells a 25lb kettlebell, not a 50lb one. The tool must not
        # present the 25lb one as the product asked about.
        out = check_inventory.invoke({"product": "Kettlebell 50lb"})
        self.assertIn("No exact match", out)
        self.assertIn("Kettlebell 25lb Cast Iron", out)


class CatalogTests(ToolTestCase):
    def test_overview_lists_ten_categories(self):
        out = list_categories.invoke({"category": "all"})
        for cat in ["Accessories", "Beauty", "Books", "Clothing", "Electronics",
                    "Fitness", "Footwear", "Home", "Outdoor", "Toys & Games"]:
            self.assertIn(cat, out)

    def test_customer_words_find_category(self):
        self.assertEqual(list_categories.invoke({"category": "books"}).count("\n  #"), 12)

    def test_phrase_falls_back_to_product_names(self):
        out = list_categories.invoke({"category": "yoga gear"})
        self.assertIn("Yoga Mat Premium", out)
        self.assertIn("High-Waist Yoga Leggings", out)


class OrderTests(ToolTestCase):
    def test_lookup_order(self):
        out = lookup_order.invoke({"order_id": 10})
        self.assertIn("Total: $84.95", out)

    def test_missing_order(self):
        self.assertIn("No order found", lookup_order.invoke({"order_id": 9999}))


class ReturnTests(ToolTestCase):
    def test_new_return_creates_one_row(self):
        self.assertEqual(self.count_returns(14), 0)
        out = initiate_return.invoke({"order_id": 14, "reason": "speaker stopped working"})
        self.assertIn("$79.99", out)
        self.assertEqual(self.count_returns(14), 1)
        # A second request must not create a duplicate.
        self.assertIn("already exists", initiate_return.invoke({"order_id": 14, "reason": "again"}))
        self.assertEqual(self.count_returns(14), 1)

    def test_pending_order_cannot_be_returned(self):
        out = initiate_return.invoke({"order_id": 3, "reason": "changed my mind"})
        self.assertIn("Cannot process return", out)
        self.assertEqual(self.count_returns(3), 0)

    def test_existing_return_reports_reason_and_refund(self):
        # Eval queries 18 and 31 expect the existing return's reason and refund.
        out = initiate_return.invoke({"order_id": 12, "reason": "wrong color"})
        self.assertIn("already exists", out)
        self.assertIn("Sole separated after one hike", out)
        self.assertIn("$149.99", out)


if __name__ == "__main__":
    unittest.main()
