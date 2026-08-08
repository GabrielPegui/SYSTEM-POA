"""Domain entities.

The domain layer is independent of SQLAlchemy, FastAPI and any
infrastructure detail. Entities are immutable dataclasses.
"""

from app.domain.entities.customer import Customer
from app.domain.entities.order import Order
from app.domain.entities.order_item import OrderItem
from app.domain.entities.product import Product
from app.domain.entities.route import Route

__all__ = ["Customer", "Order", "OrderItem", "Product", "Route"]
