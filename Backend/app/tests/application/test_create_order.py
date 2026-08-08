"""Tests for the CreateOrder use case."""

from dataclasses import replace

import pytest

from app.application.commands import CreateOrderItemCommand
from app.application.errors import (
    CustomerNotFoundError,
    ProductNotFoundError,
    RouteNotFoundError,
)
from app.application.use_cases import CreateOrder
from app.domain.entities import Customer, Route
from app.domain.exceptions import DomainValidationError
from app.tests.application.fakes import (
    FailingOrderRepository,
    InMemoryCustomerRepository,
    InMemoryProductRepository,
    InMemoryRouteRepository,
)


def test_create_order_success(create_order, create_order_command) -> None:
    saved = create_order.execute(create_order_command)

    assert saved.id is not None
    assert saved.order_number == "12653"
    assert saved.customer.code == "CL000168"
    assert saved.customer.route.code == "PPN002"
    assert len(saved.items) == 1
    assert saved.items[0].product.code == "01010101"
    assert saved.items[0].quantity == 6


def test_create_order_multiple_items(create_order, create_order_command, product) -> None:
    command = replace(
        create_order_command,
        items=(
            CreateOrderItemCommand(product_code=product.code, quantity=6),
            CreateOrderItemCommand(product_code=product.code, quantity=12),
        ),
    )

    saved = create_order.execute(command)

    assert len(saved.items) == 2
    assert [i.quantity for i in saved.items] == [6, 12]


def test_create_order_customer_not_found(create_order, create_order_command) -> None:
    command = replace(create_order_command, customer_code="CL999999")

    with pytest.raises(CustomerNotFoundError):
        create_order.execute(command)


def test_create_order_route_not_found(create_order_command, order_repo) -> None:
    ghost_customer = Customer(
        code="CL000999", name="GHOST CLIENT", route=Route(code="PPN999", name="No Route")
    )
    use_case = CreateOrder(
        InMemoryCustomerRepository([ghost_customer]),
        InMemoryRouteRepository(),
        InMemoryProductRepository(),
        order_repo,
    )
    command = replace(create_order_command, customer_code="CL000999")

    with pytest.raises(RouteNotFoundError):
        use_case.execute(command)


def test_create_order_product_not_found(create_order, create_order_command) -> None:
    command = replace(
        create_order_command,
        items=(CreateOrderItemCommand(product_code="01019999", quantity=6),),
    )

    with pytest.raises(ProductNotFoundError):
        create_order.execute(command)


@pytest.mark.parametrize("quantity", [0, -5])
def test_create_order_invalid_quantity(create_order, create_order_command, quantity) -> None:
    command = replace(
        create_order_command,
        items=(CreateOrderItemCommand(product_code="01010101", quantity=quantity),),
    )

    with pytest.raises(DomainValidationError):
        create_order.execute(command)


def test_create_order_without_items_raises(create_order, create_order_command) -> None:
    command = replace(create_order_command, items=())

    with pytest.raises(DomainValidationError):
        create_order.execute(command)


def test_create_order_propagates_persistence_errors(create_order_command, product, customer) -> None:
    failing = FailingOrderRepository(RuntimeError("database unavailable"))
    use_case = CreateOrder(
        InMemoryCustomerRepository([customer]),
        InMemoryRouteRepository([customer.route]),
        InMemoryProductRepository([product]),
        failing,
    )

    with pytest.raises(RuntimeError, match="database unavailable"):
        use_case.execute(create_order_command)
