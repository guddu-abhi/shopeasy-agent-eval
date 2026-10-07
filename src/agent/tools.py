"""Agent tools for the e-commerce customer support bot."""

from __future__ import annotations

import re

from langchain_core.tools import tool

from src.data.database import get_connection


@tool
def lookup_order(order_id: int) -> str:
    """Find order information and status details. Use this to get data about an order."""
    conn = get_connection()
    order = conn.execute(
        "SELECT o.id, o.status, o.created_at, o.total, c.name, c.email "
        "FROM orders o JOIN customers c ON o.customer_id = c.id "
        "WHERE o.id = ?",
        (order_id,),
    ).fetchone()
    if not order:
        return f"No order found with ID {order_id}."

    items = conn.execute(
        "SELECT product_name, quantity, unit_price FROM order_items WHERE order_id = ?",
        (order_id,),
    ).fetchall()
    conn.close()

    items_str = "\n".join(
        f"  - {r['product_name']} (qty: {r['quantity']}, ${r['unit_price']:.2f})"
        for r in items
    )
    return (
        f"Order #{order['id']}\n"
        f"Customer: {order['name']} ({order['email']})\n"
        f"Status: {order['status']}\n"
        f"Date: {order['created_at']}\n"
        f"Total: ${order['total']:.2f}\n"
        f"Items:\n{items_str}"
    )


@tool
def search_orders(query: str) -> str:
    """Find orders matching the query. Returns a list of orders."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT o.id, o.status, o.created_at, o.total, c.name, c.email "
        "FROM orders o JOIN customers c ON o.customer_id = c.id "
        "WHERE c.email = ? "
        "ORDER BY o.created_at DESC",
        (query,),
    ).fetchall()
    conn.close()

    if not rows:
        return f"No orders found for '{query}'."

    lines = []
    for r in rows:
        lines.append(
            f"  Order #{r['id']}: {r['status']} — ${r['total']:.2f} ({r['created_at']})"
        )
    return f"Orders for {rows[0]['name']} ({rows[0]['email']}):\n" + "\n".join(lines)


# Words customers add around a product type ("yoga gear", "fitness equipment").
_FILLER_WORDS = {
    "a", "all", "an", "and", "any", "anything", "for", "gear", "item", "of",
    "product", "related", "some", "stuff", "supplie", "the", "thing", "equipment",
}


def _keywords(text: str) -> list[str]:
    """Lowercase words with a trailing "s" removed, minus filler words."""
    words = []
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if len(w) > 3 and w.endswith("s"):
            w = w[:-1]
        if w not in _FILLER_WORDS:
            words.append(w)
    return words


def _find_products(conn, product: str, columns: str) -> list:
    """Find products by ID ("33", "#33", "product 33") or by name. A name returns
    the exact match if there is one, else the products whose names share the
    most keywords with it (at most 5)."""
    m = re.fullmatch(r"\s*(?:product\s*)?(?:id\s*)?#?\s*(\d+)\s*", product, re.IGNORECASE)
    if m:
        return conn.execute(
            f"SELECT {columns} FROM products WHERE id = ?", (int(m.group(1)),)
        ).fetchall()

    exact = conn.execute(
        f"SELECT {columns} FROM products WHERE lower(name) = ?",
        (product.strip().lower(),),
    ).fetchall()
    if exact:
        return exact

    keywords = _keywords(product)
    rows = conn.execute(f"SELECT {columns} FROM products").fetchall()
    scored = [(sum(k in r["name"].lower() for k in keywords), r) for r in rows]
    best = max((n for n, _ in scored), default=0)
    if best == 0:
        return []
    return [r for n, r in scored if n == best][:5]


@tool
def get_product_details(product: str) -> str:
    """Get a product's name, category, price, and description. Pass the product's
    ID (e.g. "33") or its name (e.g. "Vacuum Insulated Tumbler")."""
    conn = get_connection()
    rows = _find_products(conn, product, "id, name, category, price, description")
    conn.close()

    if not rows:
        return f"No product found matching '{product}'."

    return "\n\n".join(
        f"Product #{row['id']}: {row['name']}\n"
        f"Category: {row['category']}\n"
        f"Price: ${row['price']:.2f}\n"
        f"Description: {row['description']}"
        for row in rows
    )


@tool
def search_products(query: str) -> str:
    """Look up products in the system. Use this to find product data."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, name, category, price FROM products "
        "WHERE name LIKE ? OR category LIKE ?",
        (f"%{query}%", f"%{query}%"),
    ).fetchall()
    conn.close()

    if not rows:
        return f"No products found matching '{query}'."

    lines = [
        f"  #{r['id']}: {r['name']} ({r['category']}) — ${r['price']:.2f}"
        for r in rows
    ]
    return f"Products matching '{query}':\n" + "\n".join(lines)


@tool
def list_categories(category: str) -> str:
    """List the store's catalog. Pass a category or kind of product (e.g.
    "Footwear", "books", "toys", "yoga") to get the matching in-stock products.
    Pass "all" to get every category with product counts and price ranges. Use
    this when the customer asks what the store sells, what categories exist, or
    which products of a kind are available."""
    conn = get_connection()
    products = conn.execute(
        "SELECT id, name, category, price FROM products "
        "WHERE stock_quantity > 0 ORDER BY name"
    ).fetchall()
    conn.close()

    # Loose keyword match, so "books" finds "Books", "toys" finds "Toys & Games",
    # and "yoga gear" finds products named "Yoga ...".
    keywords = _keywords(category)
    if keywords:
        in_category = [
            p for p in products
            if any(k in p["category"].lower() for k in keywords)
        ]
        if in_category:
            lines = [f"  #{p['id']}: {p['name']} — ${p['price']:.2f}" for p in in_category]
            return f"Products in {category}:\n" + "\n".join(lines)

        # Not a category: fall back to products whose name has a keyword,
        # best matches first.
        hits = [(sum(k in p["name"].lower() for k in keywords), p) for p in products]
        by_name = [p for n, p in sorted(hits, key=lambda h: -h[0]) if n > 0]
        if by_name:
            lines = [
                f"  #{p['id']}: {p['name']} ({p['category']}) — ${p['price']:.2f}"
                for p in by_name
            ]
            return f"In-stock products matching '{category}':\n" + "\n".join(lines)

    counts: dict[str, list[float]] = {}
    for p in products:
        counts.setdefault(p["category"], []).append(p["price"])
    lines = [
        f"  - {c}: {len(prices)} products (${min(prices):.2f}–${max(prices):.2f})"
        for c, prices in sorted(counts.items())
    ]
    header = "Store categories:"
    if keywords:
        header = f"'{category}' is not a category or product name. Here are all store categories:"
    return header + "\n" + "\n".join(lines)


@tool
def check_inventory(product: str) -> str:
    """Check whether a product is in stock and how many units are available. Pass
    the product's ID (e.g. "159") or its name (e.g. "Kettlebell 25lb Cast Iron")."""
    conn = get_connection()
    rows = _find_products(conn, product, "id, name, stock_quantity")
    conn.close()

    if not rows:
        return f"No product found matching '{product}'."

    return "\n\n".join(
        f"Product #{row['id']}: {row['name']}\n"
        f"In stock: {'Yes' if row['stock_quantity'] > 0 else 'No'}\n"
        f"Quantity available: {row['stock_quantity']}"
        for row in rows
    )


@tool
def get_shipping_status(order_id: int) -> str:
    """Get order status and delivery information. Use this for order updates."""
    conn = get_connection()
    row = conn.execute(
        "SELECT s.carrier, s.tracking_number, s.status, s.estimated_delivery, "
        "s.shipped_at, o.status as order_status "
        "FROM shipping s JOIN orders o ON s.order_id = o.id "
        "WHERE s.order_id = ?",
        (order_id,),
    ).fetchone()
    conn.close()

    if not row:
        return f"No shipping information found for order #{order_id}. The order may not have shipped yet."

    return (
        f"Shipping for Order #{order_id}\n"
        f"Order status: {row['order_status']}\n"
        f"Carrier: {row['carrier']}\n"
        f"Tracking number: {row['tracking_number']}\n"
        f"Shipping status: {row['status']}\n"
        f"Shipped: {row['shipped_at']}\n"
        f"Estimated delivery: {row['estimated_delivery']}"
    )


@tool
def initiate_return(order_id: int, reason: str) -> str:
    """Handle a customer issue with an order. Use this when a customer has a problem."""
    conn = get_connection()

    # Check order exists
    order = conn.execute(
        "SELECT id, status, total FROM orders WHERE id = ?",
        (order_id,),
    ).fetchone()
    if not order:
        conn.close()
        return f"No order found with ID {order_id}."

    if order["status"] not in ("delivered", "shipped"):
        conn.close()
        return f"Cannot process return for order #{order_id}: order status is '{order['status']}'. Only shipped or delivered orders can be returned."

    # Check if return already exists
    existing = conn.execute(
        "SELECT id, status FROM returns WHERE order_id = ?",
        (order_id,),
    ).fetchone()
    if existing:
        conn.close()
        return f"A return request already exists for order #{order_id} (Return #{existing['id']}, status: {existing['status']})."

    cur = conn.execute(
        "INSERT INTO returns (order_id, reason, status, refund_amount) VALUES (?, ?, 'requested', ?)",
        (order_id, reason, order["total"]),
    )
    conn.commit()
    return_id = cur.lastrowid
    conn.close()

    return (
        f"Return request created successfully.\n"
        f"Return #{return_id} for Order #{order_id}\n"
        f"Reason: {reason}\n"
        f"Status: requested\n"
        f"Refund amount: ${order['total']:.2f} (pending approval)"
    )


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
