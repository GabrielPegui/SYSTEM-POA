"""Shared fixtures for application layer tests.

All tests run against in-memory fakes: no database is required.
"""

from datetime import date

import pytest

from app.application.commands import CreateOrderCommand, CreateOrderItemCommand
from app.application.use_cases import CreateOrder, GetOrder, ListOrders, ValidateOrder
from app.domain.entities import Customer, Order, OrderItem, Route
from app.tests.application.fakes import (
    InMemoryCustomerRepository,
    InMemoryOrderRepository,
    InMemoryRouteRepository,
)


@pytest.fixture
def route() -> Route:
    return Route(code="PPN002", name="Ozama")


@pytest.fixture
def customer(route: Route) -> Customer:
    return Customer(
        name="JASON FAST FOOD", route=route, address="Av. 27 de Febrero 200"
    )


@pytest.fixture
def order_item() -> OrderItem:
    return OrderItem(description="VIGA MEDIANA BLANCO PEPIN", quantity=6)


@pytest.fixture
def order(customer: Customer, order_item: OrderItem) -> Order:
    return Order(
        order_number="12653",
        customer=customer,
        delivery_date=date(2026, 8, 10),
        items=(order_item,),
    )


@pytest.fixture
def route_repo(route: Route) -> InMemoryRouteRepository:
    return InMemoryRouteRepository([route])


@pytest.fixture
def customer_repo(customer: Customer) -> InMemoryCustomerRepository:
    return InMemoryCustomerRepository([customer])


@pytest.fixture
def order_repo() -> InMemoryOrderRepository:
    return InMemoryOrderRepository()


@pytest.fixture
def create_order(
    customer_repo: InMemoryCustomerRepository,
    order_repo: InMemoryOrderRepository,
) -> CreateOrder:
    return CreateOrder(customer_repo, order_repo)


@pytest.fixture
def get_order(order_repo: InMemoryOrderRepository) -> GetOrder:
    return GetOrder(order_repo)


@pytest.fixture
def validate_order(order_repo: InMemoryOrderRepository) -> ValidateOrder:
    return ValidateOrder(order_repo)


@pytest.fixture
def list_orders(order_repo: InMemoryOrderRepository) -> ListOrders:
    return ListOrders(order_repo)


@pytest.fixture
def create_order_command(order: Order) -> CreateOrderCommand:
    item = order.items[0]
    return CreateOrderCommand(
        order_number=order.order_number,
        customer_name=order.customer.name,
        delivery_date=order.delivery_date,
        items=(CreateOrderItemCommand(description=item.description, quantity=item.quantity),),
    )
