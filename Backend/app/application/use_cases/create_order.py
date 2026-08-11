"""CreateOrder use case.

Registers a valid, structured purchase order. Input is expected to be already
structured: no PDF reading, parsing, fuzzy matching or OCR happen here
(ADR-002). The customer is resolved by name from the catalog (the business
key of the definitive model). Because equal names can exist on different
routes, an ambiguous name raises ``AmbiguousCustomerError``.
"""

from app.application.commands import CreateOrderCommand, CreateOrderItemCommand
from app.application.errors import (
    AmbiguousCustomerError,
    CustomerNotFoundError,
)
from app.domain.entities import Order, OrderItem
from app.domain.interfaces.repositories import (
    CustomerRepository,
    OrderRepository,
)


class CreateOrder:
    """Use case that persists a new order from structured input."""

    def __init__(
        self,
        customers: CustomerRepository,
        orders: OrderRepository,
    ) -> None:
        self._customers = customers
        self._orders = orders

    def execute(self, command: CreateOrderCommand) -> Order:
        matches = self._customers.get_by_name(command.customer_name)
        if not matches:
            raise CustomerNotFoundError(command.customer_name)
        if len(matches) > 1:
            raise AmbiguousCustomerError(
                command.customer_name, tuple(c.route.code for c in matches)
            )
        customer = matches[0]

        order = Order(
            order_number=command.order_number,
            customer=customer,
            delivery_date=command.delivery_date,
            items=tuple(self._to_item(item) for item in command.items),
        )
        return self._orders.save(order)

    @staticmethod
    def _to_item(item: CreateOrderItemCommand) -> OrderItem:
        return OrderItem(
            description=item.description,
            quantity=item.quantity,
            pdf_code=item.pdf_code,
            ean=item.ean,
        )
