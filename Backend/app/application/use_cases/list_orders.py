"""ListOrders use case.

Retrieves the persisted orders (newest first) through the order repository
contract. Kept intentionally thin: no filtering or pagination in the MVP;
the repository returns a plain list.
"""

from app.domain.entities import Order
from app.domain.interfaces.repositories import OrderRepository


class ListOrders:
    """Use case that lists the persisted orders."""

    def __init__(self, orders: OrderRepository) -> None:
        self._orders = orders

    def execute(self) -> list[Order]:
        return self._orders.list()
