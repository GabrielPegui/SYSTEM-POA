"""CreateOrder use case.

Registers a valid, structured purchase order. Input is expected to be already
structured: no PDF reading, parsing, fuzzy matching or OCR happen here
(ADR-002). References (customer, route, products) are resolved through the
repository contracts and must exist; the route is verified through the route
of the resolved customer (1:1 rule).
"""

from app.application.commands import CreateOrderCommand, CreateOrderItemCommand
from app.application.errors import (
    CustomerNotFoundError,
    ProductNotFoundError,
    RouteNotFoundError,
)
from app.domain.entities import Order, OrderItem
from app.domain.interfaces.repositories import (
    CustomerRepository,
    OrderRepository,
    ProductRepository,
    RouteRepository,
)


class CreateOrder:
    """Use case that persists a new order from structured input."""

    def __init__(
        self,
        customers: CustomerRepository,
        routes: RouteRepository,
        products: ProductRepository,
        orders: OrderRepository,
    ) -> None:
        self._customers = customers
        self._routes = routes
        self._products = products
        self._orders = orders

    def execute(self, command: CreateOrderCommand) -> Order:
        customer = self._customers.get_by_code(command.customer_code)
        if customer is None:
            raise CustomerNotFoundError(command.customer_code)

        route = self._routes.get_by_code(customer.route.code)
        if route is None:
            raise RouteNotFoundError(customer.route.code)

        items = tuple(self._resolve_item(item) for item in command.items)

        order = Order(
            order_number=command.order_number,
            customer=customer,
            delivery_date=command.delivery_date,
            items=items,
        )
        return self._orders.save(order)

    def _resolve_item(self, item: CreateOrderItemCommand) -> OrderItem:
        product = self._products.get_by_code(item.product_code)
        if product is None:
            raise ProductNotFoundError(item.product_code)
        return OrderItem(product=product, quantity=item.quantity)
