"""ValidateOrder use case.

Represents the human/operational validation of an order:

    Order processed
          ↓
    Human review
          ↓
    Order validated

Transition rule (documented in this sprint): an order can be validated from
``PROCESSED`` (freshly produced by the processing pipeline) or
``PENDING_VALIDATION`` (explicitly queued for review) to ``VALIDATED``.
Orders already ``VALIDATED`` or in ``ERROR`` cannot be validated.

The automatic transition ``PROCESSED -> PENDING_VALIDATION`` (queuing an
order for review right after parsing) is part of the order-processing
workflow, not of this use case.
"""

from app.application.errors import (
    InvalidOrderStatusTransitionError,
    OrderNotFoundError,
)
from app.domain.entities import Order
from app.domain.enums import OrderStatus
from app.domain.interfaces.repositories import OrderRepository


class ValidateOrder:
    """Use case that validates an order after human review."""

    _VALIDATABLE_STATES = frozenset({OrderStatus.PROCESSED, OrderStatus.PENDING_VALIDATION})

    def __init__(self, orders: OrderRepository) -> None:
        self._orders = orders

    def execute(self, order_number: str) -> Order:
        order = self._orders.get_by_number(order_number)
        if order is None:
            raise OrderNotFoundError(order_number)
        if order.status not in self._VALIDATABLE_STATES:
            raise InvalidOrderStatusTransitionError(order.status, OrderStatus.VALIDATED)
        return self._orders.update_status(order.id, OrderStatus.VALIDATED)
