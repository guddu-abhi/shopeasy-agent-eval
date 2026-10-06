"""Agent tools for the e-commerce customer support bot."""

from __future__ import annotations

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


@tool
def get_product_details(product_id: int) -> str:
    """Get information about an item. Returns details for the requested item."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, name, category, price, description FROM products WHERE id = ?",
        (product_id,),
    ).fetchone()
    conn.close()

    if not row:
        return f"No product found with ID {product_id}."

    return (
        f"Product #{row['id']}: {row['name']}\n"
        f"Category: {row['category']}\n"
        f"Price: ${row['price']:.2f}\n"
        f"Description: {row['description']}"
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
def check_inventory(product_id: int) -> str:
    """Check product availability. Use this to see if a product is available."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, name, stock_quantity FROM products WHERE id = ?",
        (product_id,),
    ).fetchone()
    conn.close()

    if not row:
        return f"No product found with ID {product_id}."

    in_stock = row["stock_quantity"] > 0
    return (
        f"Product #{row['id']}: {row['name']}\n"
        f"In stock: {'Yes' if in_stock else 'No'}\n"
        f"Quantity available: {row['stock_quantity']}"
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
    check_inventory,
    get_shipping_status,
    initiate_return,
]
