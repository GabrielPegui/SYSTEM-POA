"""Tests for the CreateOrder use case."""

from dataclasses import replace

import pytest

from app.application.commands import CreateOrderItemCommand
from app.application.errors import (
    AmbiguousCustomerError,
    CustomerNotFoundError,
)
from app.application.use_cases import CreateOrder
from app.domain.entities import Customer, Route
from app.domain.exceptions import DomainValidationError
from app.tests.application.fakes import (
    FailingOrderRepository,
    InMemoryCustomerRepository,
    InMemoryOrderRepository,
)


def test_create_order_success(create_order, create_order_command) -> None:
    saved = create_order.execute(create_order_command)

    assert saved.id is not None
    assert saved.order_number == "12653"
    assert saved.customer.name == "JASON FAST FOOD"
    assert saved.customer.route.code == "PPN002"
    assert len(saved.items) == 1
    assert saved.items[0].description == "VIGA MEDIANA BLANCO PEPIN"
    assert saved.items[0].quantity == 6


def test_create_order_multiple_items(create_order, create_order_command) -> None:
    command = replace(
        create_order_command,
        items=(
            CreateOrderItemCommand(description="VIGA MEDIANA BLANCO PEPIN", quantity=6),
            CreateOrderItemCommand(description="VIGA MEDIANA BLANCO PEPIN", quantity=12),
        ),
    )

    saved = create_order.execute(command)

    assert len(saved.items) == 2
    assert [i.quantity for i in saved.items] == [6, 12]


def test_create_order_customer_not_found(create_order, create_order_command) -> None:
    command = replace(create_order_command, customer_name="CLIENTE INEXISTENTE")

    with pytest.raises(CustomerNotFoundError):
        create_order.execute(command)


def test_create_order_ambiguous_customer_raises(create_order_command) -> None:
    route_1 = Route(code="PPN303", name="Ruta A")
    route_2 = Route(code="PPN601", name="Ruta B")
    duplicated = [
        Customer(name="INVERSIONES LLERS", route=route_1),
        Customer(name="INVERSIONES LLERS", route=route_2),
    ]
    use_case = CreateOrder(
        InMemoryCustomerRepository(duplicated),
        InMemoryOrderRepository(),
    )
    command = replace(create_order_command, customer_name="INVERSIONES LLERS")

    with pytest.raises(AmbiguousCustomerError):
        use_case.execute(command)


@pytest.mark.parametrize("quantity", [0, -5])
def test_create_order_invalid_quantity(create_order, create_order_command, quantity) -> None:
    command = replace(
        create_order_command,
        items=(CreateOrderItemCommand(description="VIGA MEDIANA BLANCO PEPIN", quantity=quantity),),
    )

    with pytest.raises(DomainValidationError):
        create_order.execute(command)


def test_create_order_without_items_raises(create_order, create_order_command) -> None:
    command = replace(create_order_command, items=())

    with pytest.raises(DomainValidationError):
        create_order.execute(command)


def test_create_order_propagates_persistence_errors(create_order_command, customer) -> None:
    failing = FailingOrderRepository(RuntimeError("database unavailable"))
    use_case = CreateOrder(
        InMemoryCustomerRepository([customer]),
        failing,
    )

    with pytest.raises(RuntimeError, match="database unavailable"):
        use_case.execute(create_order_command)
