"""Shared fixtures for domain tests."""

from datetime import date

import pytest

from app.domain.entities import Customer, Order, OrderItem, Route


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
