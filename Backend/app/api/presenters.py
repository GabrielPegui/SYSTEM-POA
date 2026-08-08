"""Presenters: map domain entities to API response schemas.

This mapping belongs to the presentation layer (ADR-001/ADR-003): domain
entities are never exposed directly, only their DTO representation.
"""

from app.api.schemas import OrderItemResponse, OrderResponse
from app.domain.entities import Order


def to_order_response(order: Order) -> OrderResponse:
    """Convert a domain order into its API representation."""
    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        customer_code=order.customer.code,
        customer_name=order.customer.name,
        route_code=order.customer.route.code,
        delivery_date=order.delivery_date,
        status=order.status,
        items=[
            OrderItemResponse(
                product_code=item.product.code,
                product_description=item.product.description,
                quantity=item.quantity,
            )
            for item in order.items
        ],
    )
