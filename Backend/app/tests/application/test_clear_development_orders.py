"""Tests for the ClearDevelopmentOrders use case.

The use case deletes every persisted order and its items (development-only
cleanup). It must never touch the schema: the repository (real or fake) only
removes data, and the processing history stays intact as the audit trail.
"""

from datetime import date

from app.application.use_cases import ClearDevelopmentOrders
from app.domain.entities import Customer, Order, OrderItem, Route
from app.tests.application.fakes import InMemoryOrderRepository


def _order(order_number: str, source_filename: str) -> Order:
    route = Route(code="PPN006", name="Ruta 6")
    customer = Customer(name="MERCADAL GUARICANO", route=route)
    item = OrderItem(description="PEPIN PAN HOT DOG 8/1", quantity=6)
    return Order(
        order_number=order_number,
        customer=customer,
        delivery_date=date(2026, 8, 10),
        items=(item,),
        source_filename=source_filename,
    )


def test_clear_deletes_every_order_and_returns_count() -> None:
    order_repo = InMemoryOrderRepository()
    order_repo.save(_order("4000326758", "mercadal.pdf"))
    order_repo.save(_order("4000326759", "copia_mercadal.pdf"))

    deleted = ClearDevelopmentOrders(order_repo).execute()

    assert deleted == 2
    assert order_repo.list() == []


def test_clear_empty_returns_zero() -> None:
    assert ClearDevelopmentOrders(InMemoryOrderRepository()).execute() == 0