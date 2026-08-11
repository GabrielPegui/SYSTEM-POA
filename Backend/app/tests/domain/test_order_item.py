"""Tests for the OrderItem entity."""

import pytest

from app.domain.entities import OrderItem
from app.domain.exceptions import DomainValidationError


def test_valid_order_item_creation() -> None:
    item = OrderItem(description="PEPIN PAN HOT DOG 8/1", quantity=6)

    assert item.description == "PEPIN PAN HOT DOG 8/1"
    assert item.quantity == 6
    assert item.id is None


def test_order_item_keeps_traceability_fields() -> None:
    item = OrderItem(
        description="PEPIN PAN HOT DOG 8/1",
        quantity=6,
        pdf_code="02010101",
        ean="7501000100101",
    )

    assert item.pdf_code == "02010101"
    assert item.ean == "7501000100101"


@pytest.mark.parametrize("invalid_quantity", [0, -3])
def test_order_item_non_positive_quantity_raises(invalid_quantity: int) -> None:
    with pytest.raises(DomainValidationError):
        OrderItem(description="PEPIN PAN HOT DOG 8/1", quantity=invalid_quantity)


def test_order_item_blank_description_raises() -> None:
    with pytest.raises(DomainValidationError):
        OrderItem(description="   ", quantity=6)
