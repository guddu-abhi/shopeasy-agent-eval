from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Customer:
    id: int
    name: str
    email: str
    phone: str
    created_at: str


@dataclass
class Product:
    id: int
    name: str
    category: str
    price: float
    description: str
    stock_quantity: int


@dataclass
class Order:
    id: int
    customer_id: int
    status: str  # pending, confirmed, shipped, delivered, cancelled
    created_at: str
    total: float
    items: list[OrderItem] = field(default_factory=list)


@dataclass
class OrderItem:
    id: int
    order_id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float


@dataclass
class ShippingInfo:
    id: int
    order_id: int
    carrier: str
    tracking_number: str
    status: str  # in_transit, out_for_delivery, delivered, delayed
    estimated_delivery: str
    shipped_at: str


@dataclass
class ReturnRequest:
    id: int
    order_id: int
    reason: str
    status: str  # requested, approved, rejected, completed
    created_at: str
    refund_amount: float | None = None
