"""Tests for the Order entity."""

from datetime import date

import pytest

from app.domain.entities import Order
from app.domain.enums import OrderStatus
from app.domain.exceptions import DomainValidationError


def test_valid_order_creation(order) -> None:
    assert order.order_number == "12653"
    assert order.delivery_date == date(2026, 8, 10)
    assert len(order.items) == 1
    assert order.id is None


def test_order_default_status_is_processed(order) -> None:
    assert order.status is OrderStatus.PROCESSED


def test_order_status_can_be_set(customer, order_item) -> None:
    order = Order(
        order_number="12653",
        customer=customer,
        delivery_date=date(2026, 8, 10),
        items=(order_item,),
        status=OrderStatus.PENDING_VALIDATION,
    )

    assert order.status is OrderStatus.PENDING_VALIDATION


def test_order_relationship_to_customer(order, customer) -> None:
    assert order.customer is customer
    assert order.customer.route.code == "PPN002"


def test_order_items_expose_products(order, product) -> None:
    item = order.items[0]

    assert item.product is product
    assert item.product.code == "01010101"


def test_order_with_multiple_items(customer, product) -> None:
    order = Order(
        order_number="12654",
        customer=customer,
        delivery_date=date(2026, 8, 11),
        items=(_item(product, 6), _item(product, 12)),
    )

    assert len(order.items) == 2
    assert order.items[0].quantity == 6
    assert order.items[1].quantity == 12


def test_order_blank_number_raises(customer, order_item) -> None:
    with pytest.raises(DomainValidationError):
        Order(
            order_number="",
            customer=customer,
            delivery_date=date(2026, 8, 10),
            items=(order_item,),
        )


def test_order_missing_customer_raises(order_item) -> None:
    with pytest.raises(DomainValidationError):
        Order(
            order_number="12653",
            customer=None,  # type: ignore[arg-type]
            delivery_date=date(2026, 8, 10),
            items=(order_item,),
        )


def test_order_missing_delivery_date_raises(customer, order_item) -> None:
    with pytest.raises(DomainValidationError):
        Order(
            order_number="12653",
            customer=customer,
            delivery_date=None,  # type: ignore[arg-type]
            items=(order_item,),
        )


def test_order_without_items_raises(customer) -> None:
    with pytest.raises(DomainValidationError):
        Order(
            order_number="12653",
            customer=customer,
            delivery_date=date(2026, 8, 10),
            items=(),
        )


def _item(product, quantity):
    from app.domain.entities import OrderItem

    return OrderItem(product=product, quantity=quantity)
