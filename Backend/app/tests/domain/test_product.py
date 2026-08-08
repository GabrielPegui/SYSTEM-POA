"""Tests for the Product entity."""

import pytest

from app.domain.entities import Product
from app.domain.exceptions import DomainValidationError


def test_valid_product_creation() -> None:
    product = Product(code="01010101", description="VIGA MEDIANA BLANCO PEPIN")

    assert product.code == "01010101"
    assert product.description == "VIGA MEDIANA BLANCO PEPIN"
    assert product.id is None


def test_product_blank_code_raises() -> None:
    with pytest.raises(DomainValidationError):
        Product(code="   ", description="VIGA MEDIANA BLANCO PEPIN")


def test_product_blank_description_raises() -> None:
    with pytest.raises(DomainValidationError):
        Product(code="01010101", description="")


def test_product_id_is_optional() -> None:
    product = Product(code="01010101", description="VIGA MEDIANA BLANCO PEPIN", id=42)

    assert product.id == 42
