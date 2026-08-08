"""GetOrder use case.

Retrieves an existing order by its business number through the order
repository contract.
"""

from app.application.errors import OrderNotFoundError
from app.domain.entities import Order
from app.domain.interfaces.repositories import OrderRepository


class GetOrder:
    """Use case that retrieves an existing order."""

    def __init__(self, orders: OrderRepository) -> None:
        self._orders = orders

    def execute(self, order_number: str) -> Order:
        order = self._orders.get_by_number(order_number)
        if order is None:
            raise OrderNotFoundError(order_number)
        return order
