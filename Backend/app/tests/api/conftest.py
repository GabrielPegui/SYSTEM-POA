"""Shared fixtures for API layer tests.

Endpoints are exercised through ``TestClient`` with the use-case providers
overridden by in-memory fakes (``app.tests.application.fakes``), so no SQL
Server is needed and the transport wiring can be tested in isolation.
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.api.deps import (
    get_create_order,
    get_get_order,
    get_list_orders,
    get_validate_order,
)
from app.application.use_cases import CreateOrder, GetOrder, ListOrders, ValidateOrder
from app.domain.entities import Customer, Order, OrderItem, Route
from app.main import app
from app.tests.application.fakes import (
    InMemoryCustomerRepository,
    InMemoryOrderRepository,
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
def customer_repo(customer: Customer) -> InMemoryCustomerRepository:
    return InMemoryCustomerRepository([customer])


@pytest.fixture
def order_repo() -> InMemoryOrderRepository:
    return InMemoryOrderRepository()


@pytest.fixture
def client(
    customer_repo: InMemoryCustomerRepository,
    order_repo: InMemoryOrderRepository,
) -> TestClient:
    """TestClient with the use-case providers overridden by in-memory fakes."""
    app.dependency_overrides[get_create_order] = lambda: CreateOrder(customer_repo, order_repo)
    app.dependency_overrides[get_get_order] = lambda: GetOrder(order_repo)
    app.dependency_overrides[get_list_orders] = lambda: ListOrders(order_repo)
    app.dependency_overrides[get_validate_order] = lambda: ValidateOrder(order_repo)

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client

    app.dependency_overrides.clear()
