"""Agent tools for the e-commerce customer support bot.

The module has three layers:
- Keywords turns a customer's wording into words that can be compared.
- The repositories own the SQL, one class per group of tables.
- The @tool functions fetch rows and return a result model as a dict, which
  LangChain serializes to the JSON the model reads.
"""

from __future__ import annotations

import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from typing import Annotated

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.data.database import get_connection


def _connect() -> closing[sqlite3.Connection]:
    """Open a connection that closes when the `with` block ends."""
    return closing(get_connection())


# --- Keyword matching --------------------------------------------------------


class Keywords:
    """The meaningful words of a phrase: lowercased, with a trailing "s"
    removed, and without filler words."""

    # Words customers add around a product type ("yoga gear", "fitness equipment").
    FILLER_WORDS = frozenset({
        "a", "all", "an", "and", "any", "anything", "for", "gear", "item", "of",
        "product", "related", "some", "stuff", "supplie", "the", "thing", "equipment",
    })

    def __init__(self, text: str):
        words = set()
        for w in re.findall(r"[a-z0-9]+", text.lower()):
            if len(w) > 3 and w.endswith("s"):
                w = w[:-1]
            if w not in self.FILLER_WORDS:
                words.add(w)
        self.words = frozenset(words)

    def __bool__(self) -> bool:
        return bool(self.words)

    def __len__(self) -> int:
        return len(self.words)

    def overlap(self, name: str) -> int:
        """How many of these words appear as whole words in `name`, so "air"
        does not match "Hair Clip Set"."""
        return len(self.words & Keywords(name).words)

    def in_category(self, category: str) -> bool:
        """Whether any word appears inside `category`, so "toys" matches
        "Toys & Games"."""
        return any(w in category.lower() for w in self.words)


# --- Repositories ------------------------------------------------------------


class _Repository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn


class OrderRepository(_Repository):
    """Orders, their items, and their shipping records."""

    def get(self, order_id: int) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT o.id, o.status, o.created_at, o.total, c.name, c.email "
            "FROM orders o JOIN customers c ON o.customer_id = c.id "
            "WHERE o.id = ?",
            (order_id,),
        ).fetchone()

    def items(self, order_id: int) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT product_name, quantity, unit_price FROM order_items WHERE order_id = ?",
            (order_id,),
        ).fetchall()

    def for_email(self, email: str) -> list[sqlite3.Row]:
        """The customer's orders, newest first."""
        return self._conn.execute(
            "SELECT o.id, o.status, o.created_at, o.total, c.name, c.email "
            "FROM orders o JOIN customers c ON o.customer_id = c.id "
            "WHERE c.email = ? "
            "ORDER BY o.created_at DESC",
            (email,),
        ).fetchall()

    def shipping(self, order_id: int) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT s.carrier, s.tracking_number, s.status, s.estimated_delivery, "
            "s.shipped_at, o.status as order_status "
            "FROM shipping s JOIN orders o ON s.order_id = o.id "
            "WHERE s.order_id = ?",
            (order_id,),
        ).fetchone()


class ReturnRepository(_Repository):
    def for_order(self, order_id: int) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT id, status, reason, refund_amount FROM returns WHERE order_id = ?",
            (order_id,),
        ).fetchone()

    def create(self, order_id: int, reason: str, refund_amount: float) -> int:
        """Insert a 'requested' return and return its ID."""
        cur = self._conn.execute(
            "INSERT INTO returns (order_id, reason, status, refund_amount) VALUES (?, ?, 'requested', ?)",
            (order_id, reason, refund_amount),
        )
        self._conn.commit()
        return cur.lastrowid


@dataclass(frozen=True)
class ProductMatch:
    """Products found for a reference, and whether they are what was asked for
    or only close matches."""

    rows: list[sqlite3.Row]
    exact: bool

    def note(self, product: str) -> str | None:
        if self.exact:
            return None
        return (
            f"No exact match for '{product}'. These are the closest products, not the "
            f"same item; tell the customer this before offering them."
        )


class ProductRepository(_Repository):
    def find(self, product: str, columns: str) -> ProductMatch:
        """Find products by ID ("33", "#33", "product 33") or by name. A name
        matches a product whose name contains every keyword as a whole word.
        Otherwise, the products sharing the most keywords are returned (at most
        5) as close matches only."""
        m = re.fullmatch(r"\s*(?:product\s*)?(?:id\s*)?#?\s*(\d+)\s*", product, re.IGNORECASE)
        if m:
            rows = self._conn.execute(
                f"SELECT {columns} FROM products WHERE id = ?", (int(m.group(1)),)
            ).fetchall()
            return ProductMatch(rows, exact=True)

        rows = self._conn.execute(
            f"SELECT {columns} FROM products WHERE lower(name) = ?",
            (product.strip().lower(),),
        ).fetchall()
        if rows:
            return ProductMatch(rows, exact=True)

        keywords = Keywords(product)
        rows = self._conn.execute(f"SELECT {columns} FROM products").fetchall()
        scored = [(keywords.overlap(r["name"]), r) for r in rows]
        best = max((n for n, _ in scored), default=0)
        if best == 0:
            return ProductMatch([], exact=False)
        return ProductMatch([r for n, r in scored if n == best][:5], exact=best == len(keywords))

    def search(self, query: str) -> list[sqlite3.Row]:
        """Products whose name or category contains `query`."""
        return self._conn.execute(
            "SELECT id, name, category, price FROM products "
            "WHERE name LIKE ? OR category LIKE ?",
            (f"%{query}%", f"%{query}%"),
        ).fetchall()

    def in_stock(self) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT id, name, category, price FROM products "
            "WHERE stock_quantity > 0 ORDER BY name"
        ).fetchall()


# --- Results -----------------------------------------------------------------
# Each tool returns one of these models as a dict. LangChain serializes the
# dict to JSON for the model, so the field names are the labels the model
# reads. Prices are "$9.99" strings, so the model can copy them exactly.


class Error(BaseModel):
    error: str


class LineItem(BaseModel):
    product: str
    quantity: int
    unit_price: str


class Order(BaseModel):
    order_id: int
    status: str
    order_date: str
    total: str
    customer: str | None = None
    email: str | None = None
    items: list[LineItem] | None = None


class CustomerOrders(BaseModel):
    customer: str
    email: str
    orders: list[Order]


class Product(BaseModel):
    product_id: int
    name: str
    category: str | None = None
    price: str | None = None
    description: str | None = None
    in_stock: bool | None = None
    quantity_available: int | None = None


class Products(BaseModel):
    note: str | None = None
    products: list[Product]


class Category(BaseModel):
    category: str
    product_count: int
    price_range: str


class Categories(BaseModel):
    note: str | None = None
    categories: list[Category]


class Shipping(BaseModel):
    order_id: int
    order_status: str
    carrier: str
    tracking_number: str
    shipping_status: str
    shipped_at: str | None = None
    estimated_delivery: str | None = None


class Return(BaseModel):
    note: str
    return_id: int
    order_id: int
    reason: str
    status: str
    refund_amount: str | None = None


def _result(model: BaseModel) -> dict:
    """The model as a dict without empty fields, so the JSON stays short."""
    return model.model_dump(exclude_none=True)


def _money(amount: float) -> str:
    return f"${amount:.2f}"


# --- Tools -------------------------------------------------------------------
# The model sees each tool's name, docstring, and argument descriptions, but not
# its return type, so each docstring says what the result contains.

OrderId = Annotated[int, Field(description="The order number, e.g. 14 for order #14.")]
ProductRef = Annotated[
    str, Field(description='The product ID (e.g. "33") or name (e.g. "Vacuum Insulated Tumbler").')
]


@tool
def lookup_order(order_id: OrderId) -> dict:
    """Get one order's status, order date, total, customer, and items bought. Use this
    when the customer gives an order number and asks what they bought, what it
    cost, or its status. For tracking or delivery dates, use get_shipping_status."""
    with _connect() as conn:
        orders = OrderRepository(conn)
        order = orders.get(order_id)
        items = orders.items(order_id) if order else []

    if not order:
        return _result(Error(error=f"No order found with ID {order_id}."))

    return _result(Order(
        order_id=order["id"],
        status=order["status"],
        order_date=order["created_at"],
        total=_money(order["total"]),
        customer=order["name"],
        email=order["email"],
        items=[
            LineItem(product=r["product_name"], quantity=r["quantity"], unit_price=_money(r["unit_price"]))
            for r in items
        ],
    ))


@tool
def search_orders(
    query: Annotated[str, Field(description="The customer's exact email address.")],
) -> dict:
    """List every order for a customer's email address, newest first, with each
    order's status, order date, and total. If the customer has not given an email,
    ask for it instead of calling this tool."""
    with _connect() as conn:
        rows = OrderRepository(conn).for_email(query)

    if not rows:
        return _result(Error(error=f"No orders found for '{query}'."))

    return _result(CustomerOrders(
        customer=rows[0]["name"],
        email=rows[0]["email"],
        orders=[
            Order(order_id=r["id"], status=r["status"], order_date=r["created_at"], total=_money(r["total"]))
            for r in rows
        ],
    ))


@tool
def get_product_details(product: ProductRef) -> dict:
    """Get a product's ID, name, category, price, and description. If the result
    has a `note`, the products are only close matches, not the item asked for."""
    with _connect() as conn:
        match = ProductRepository(conn).find(product, "id, name, category, price, description")

    if not match.rows:
        return _result(Error(error=f"No product found matching '{product}'."))

    return _result(Products(
        note=match.note(product),
        products=[
            Product(
                product_id=r["id"],
                name=r["name"],
                category=r["category"],
                price=_money(r["price"]),
                description=r["description"],
            )
            for r in match.rows
        ],
    ))


@tool
def search_products(
    query: Annotated[str, Field(description='One short keyword from the product name, in singular form, e.g. "headphone".')],
) -> dict:
    """Find products whose name or category contains the keyword, with each
    product's ID, name, category, and price. Use this when the customer asks
    whether the store sells something."""
    with _connect() as conn:
        rows = ProductRepository(conn).search(query)

    if not rows:
        return _result(Error(error=f"No products found matching '{query}'."))

    return _result(Products(products=[
        Product(product_id=r["id"], name=r["name"], category=r["category"], price=_money(r["price"]))
        for r in rows
    ]))


def _rank_by_name(products: list[sqlite3.Row], keywords: Keywords) -> list[sqlite3.Row]:
    """Products whose name has a keyword, best matches first."""
    hits = [(keywords.overlap(p["name"]), p) for p in products]
    return [p for n, p in sorted(hits, key=lambda h: -h[0]) if n > 0]


def _category_overview(products: list[sqlite3.Row]) -> list[Category]:
    """One entry per category, with its product count and price range."""
    prices: dict[str, list[float]] = {}
    for p in products:
        prices.setdefault(p["category"], []).append(p["price"])
    return [
        Category(category=c, product_count=len(ps), price_range=f"{_money(min(ps))}–{_money(max(ps))}")
        for c, ps in sorted(prices.items())
    ]


def _listing(products: list[sqlite3.Row], note: str | None = None) -> dict:
    return _result(Products(note=note, products=[
        Product(product_id=p["id"], name=p["name"], category=p["category"], price=_money(p["price"]))
        for p in products
    ]))


@tool
def list_categories(
    category: Annotated[str, Field(description='A category or kind of product (e.g. "Footwear", "toys", "yoga"), or "all".')],
) -> dict:
    """List the store's catalog. Pass a category or kind of product to get the
    matching in-stock products. Pass "all" to get every category with its
    product count and price range. Use this when the customer asks what the
    store sells, what categories exist, or which products of a kind are
    available."""
    with _connect() as conn:
        products = ProductRepository(conn).in_stock()

    keywords = Keywords(category)
    if keywords:
        # Loose keyword match, so "books" finds "Books" and "toys" finds "Toys & Games".
        in_category = [p for p in products if keywords.in_category(p["category"])]
        if in_category:
            return _listing(in_category)

        # Not a category: fall back to product names, so "yoga gear" finds
        # products named "Yoga ...".
        by_name = _rank_by_name(products, keywords)
        if by_name:
            return _listing(
                by_name, note=f"'{category}' is not a category. These in-stock products match it by name."
            )

    note = None
    if keywords:
        note = f"'{category}' is not a category or product name. Here are all store categories."
    return _result(Categories(note=note, categories=_category_overview(products)))


@tool
def check_inventory(product: ProductRef) -> dict:
    """Check whether a product is in stock and how many units are available. If
    the result has a `note`, the products are only close matches, not the item
    asked for."""
    with _connect() as conn:
        match = ProductRepository(conn).find(product, "id, name, stock_quantity")

    if not match.rows:
        return _result(Error(error=f"No product found matching '{product}'."))

    return _result(Products(
        note=match.note(product),
        products=[
            Product(
                product_id=r["id"],
                name=r["name"],
                in_stock=r["stock_quantity"] > 0,
                quantity_available=r["stock_quantity"],
            )
            for r in match.rows
        ],
    ))


@tool
def get_shipping_status(order_id: OrderId) -> dict:
    """Get an order's shipment: carrier, tracking number, shipping status, ship
    date, and estimated delivery. Use this when the customer asks where an
    order is, who delivers it, when it arrives, or for a tracking number."""
    with _connect() as conn:
        row = OrderRepository(conn).shipping(order_id)

    if not row:
        return _result(Error(
            error=f"No shipping information found for order #{order_id}. The order may not have shipped yet."
        ))

    return _result(Shipping(
        order_id=order_id,
        order_status=row["order_status"],
        carrier=row["carrier"],
        tracking_number=row["tracking_number"],
        shipping_status=row["status"],
        shipped_at=row["shipped_at"],
        estimated_delivery=row["estimated_delivery"],
    ))


# Only orders in these states can be returned.
_RETURNABLE_STATUSES = ("delivered", "shipped")


@tool
def initiate_return(
    order_id: OrderId,
    reason: Annotated[str, Field(description="Why the customer is returning the order, in their words.")],
) -> dict:
    """Start a return and refund request for a shipped or delivered order. Use
    this only when the customer asks to return or send back an order. Returns
    the return's ID, status, and refund amount. If a return already exists, no
    new one is created and the existing one is returned. If the order cannot be
    returned, the result has an `error` that explains why."""
    with _connect() as conn:
        order = OrderRepository(conn).get(order_id)
        if not order:
            return _result(Error(error=f"No order found with ID {order_id}."))

        if order["status"] not in _RETURNABLE_STATUSES:
            return _result(Error(
                error=f"Cannot process return for order #{order_id}: order status is "
                f"'{order['status']}'. Only shipped or delivered orders can be returned."
            ))

        returns = ReturnRepository(conn)
        existing = returns.for_order(order_id)
        if existing:
            refund = existing["refund_amount"]
            return _result(Return(
                note=f"A return request already exists for order #{order_id}. No new return was created.",
                return_id=existing["id"],
                order_id=order_id,
                reason=existing["reason"],
                status=existing["status"],
                refund_amount=_money(refund) if refund is not None else None,
            ))

        return_id = returns.create(order_id, reason, order["total"])

    return _result(Return(
        note="Return request created. The refund is pending approval.",
        return_id=return_id,
        order_id=order_id,
        reason=reason,
        status="requested",
        refund_amount=_money(order["total"]),
    ))


ALL_TOOLS = [
    lookup_order,
    search_orders,
    get_product_details,
    search_products,
    list_categories,
    check_inventory,
    get_shipping_status,
    initiate_return,
]
