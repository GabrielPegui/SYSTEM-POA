"""Tests for the Customer entity."""

import pytest

from app.domain.entities import Customer
from app.domain.exceptions import DomainValidationError


def test_valid_customer_creation(route) -> None:
    customer = Customer(code="CL000168", name="JASON FAST FOOD", route=route)

    assert customer.code == "CL000168"
    assert customer.name == "JASON FAST FOOD"
    assert customer.route is route
    assert customer.id is None


def test_customer_belongs_to_a_route(route) -> None:
    customer = Customer(code="CL000168", name="JASON FAST FOOD", route=route)

    assert customer.route.code == "PPN002"


def test_customer_blank_code_raises(route) -> None:
    with pytest.raises(DomainValidationError):
        Customer(code="", name="JASON FAST FOOD", route=route)


def test_customer_blank_name_raises(route) -> None:
    with pytest.raises(DomainValidationError):
        Customer(code="CL000168", name="   ", route=route)


def test_customer_missing_route_raises() -> None:
    with pytest.raises(DomainValidationError):
        Customer(code="CL000168", name="JASON FAST FOOD", route=None)  # type: ignore[arg-type]
