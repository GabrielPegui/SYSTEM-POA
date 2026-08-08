"""Purchase order HTTP endpoints.

The router is a thin transport layer (ADR-001): it maps request schemas onto
application commands, delegates to the use cases provided by dependency
injection, and returns DTOs. It contains no business rules, no direct
database access and no domain validation.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_create_order, get_get_order, get_list_orders, get_validate_order
from app.api.presenters import to_order_response
from app.api.schemas import CreateOrderRequest, OrderResponse
from app.application.commands import CreateOrderCommand, CreateOrderItemCommand
from app.application.use_cases import CreateOrder, GetOrder, ListOrders, ValidateOrder

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a purchase order",
)
def create_order(
    payload: CreateOrderRequest,
    use_case: Annotated[CreateOrder, Depends(get_create_order)],
) -> OrderResponse:
    """Register a structured purchase order and return it."""
    command = CreateOrderCommand(
        order_number=payload.order_number,
        customer_code=payload.customer_code,
        delivery_date=payload.delivery_date,
        items=tuple(
            CreateOrderItemCommand(product_code=item.product_code, quantity=item.quantity)
            for item in payload.items
        ),
    )
    return to_order_response(use_case.execute(command))


@router.get(
    "/{order_number}",
    response_model=OrderResponse,
    summary="Get an order by its business number",
)
def get_order(
    order_number: str,
    use_case: Annotated[GetOrder, Depends(get_get_order)],
) -> OrderResponse:
    """Return the order matching the given business number."""
    return to_order_response(use_case.execute(order_number))


@router.get(
    "",
    response_model=list[OrderResponse],
    summary="List orders",
)
def list_orders(
    use_case: Annotated[ListOrders, Depends(get_list_orders)],
) -> list[OrderResponse]:
    """Return the persisted orders, newest first."""
    return [to_order_response(order) for order in use_case.execute()]


@router.put(
    "/{order_number}/validate",
    response_model=OrderResponse,
    summary="Validate an order after human review",
)
def validate_order(
    order_number: str,
    use_case: Annotated[ValidateOrder, Depends(get_validate_order)],
) -> OrderResponse:
    """Validate the order matching the given business number."""
    return to_order_response(use_case.execute(order_number))
