"""Mappers between domain entities and SQLAlchemy models.

The domain layer never depends on the ORM. Mapping happens at the edges of
the infrastructure layer so repositories can return domain entities while
persisting with SQLAlchemy models (ADR-001, ADR-003).
"""

from app.domain.entities import Customer, Order, OrderItem, Product, Route
from app.domain.enums import OrderStatus
from app.infrastructure.persistence.models import (
    CustomerModel,
    OrderItemModel,
    OrderModel,
    ProductModel,
    RouteModel,
)


def route_to_domain(model: RouteModel) -> Route:
    """Convert a route ORM model to a domain entity."""
    return Route(code=model.code, name=model.name, id=model.id)


def customer_to_domain(model: CustomerModel) -> Customer:
    """Convert a customer ORM model to a domain entity (route included)."""
    return Customer(
        code=model.code,
        name=model.name,
        route=route_to_domain(model.route),
        id=model.id,
    )


def product_to_domain(model: ProductModel) -> Product:
    """Convert a product ORM model to a domain entity."""
    return Product(code=model.code, description=model.description, id=model.id)


def order_to_domain(model: OrderModel) -> Order:
    """Convert an order ORM model to a domain entity (aggregate).

    Requires the relationships ``customer.route`` and ``items.product`` to be
    loaded (the repositories use eager loading).
    """
    return Order(
        order_number=model.order_number,
        customer=customer_to_domain(model.customer),
        delivery_date=model.delivery_date,
        items=tuple(
            OrderItem(
                product=product_to_domain(item.product),
                quantity=item.quantity,
                id=item.id,
            )
            for item in model.items
        ),
        status=OrderStatus(model.status),
        id=model.id,
    )


def domain_to_item_model(product_model: ProductModel, item: OrderItem) -> OrderItemModel:
    """Build an order item ORM model from a domain item and a persisted product."""
    return OrderItemModel(product_id=product_model.id, quantity=item.quantity)
