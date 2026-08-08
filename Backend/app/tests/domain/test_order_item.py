"""Tests for the OrderItem entity."""

import pytest

from app.domain.entities import OrderItem
from app.domain.exceptions import DomainValidationError


def test_valid_order_item_creation(product) -> None:
    item = OrderItem(product=product, quantity=6)

    assert item.product is product
    assert item.quantity == 6
    assert item.id is None


@pytest.mark.parametrize("invalid_quantity", [0, -3])
def test_order_item_non_positive_quantity_raises(product, invalid_quantity: int) -> None:
    with pytest.raises(DomainValidationError):
        OrderItem(product=product, quantity=invalid_quantity)


def test_order_item_missing_product_raises() -> None:
    with pytest.raises(DomainValidationError):
        OrderItem(product=None, quantity=6)  # type: ignore[arg-type]
