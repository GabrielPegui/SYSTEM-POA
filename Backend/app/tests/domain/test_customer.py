"""Tests for the Customer entity."""

import pytest

from app.domain.entities import Customer
from app.domain.exceptions import DomainValidationError


def test_valid_customer_creation(route) -> None:
    customer = Customer(name="JASON FAST FOOD", route=route, address="Av. 27 de Febrero")

    assert customer.name == "JASON FAST FOOD"
    assert customer.route is route
    assert customer.address == "Av. 27 de Febrero"
    assert customer.id is None


def test_customer_address_is_optional(route) -> None:
    customer = Customer(name="JASON FAST FOOD", route=route)

    assert customer.address is None


def test_customer_belongs_to_a_route(route) -> None:
    customer = Customer(name="JASON FAST FOOD", route=route)

    assert customer.route.code == "PPN002"


def test_customer_blank_name_raises(route) -> None:
    with pytest.raises(DomainValidationError):
        Customer(name="   ", route=route)


def test_customer_missing_route_raises() -> None:
    with pytest.raises(DomainValidationError):
        Customer(name="JASON FAST FOOD", route=None)  # type: ignore[arg-type]


def test_customer_invalid_id_raises(route) -> None:
    with pytest.raises(DomainValidationError):
        Customer(name="JASON FAST FOOD", route=route, id=0)
