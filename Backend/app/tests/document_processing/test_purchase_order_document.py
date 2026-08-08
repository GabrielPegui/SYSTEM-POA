"""Tests for the standard parser output model (ADR-002).

Verifies the contract every format-specific parser must satisfy:
``PurchaseOrderDocument`` is a normalized, format-independent structure that
only carries extraction results, keeps ``quantity`` as an integer and
represents monetary values as ``Decimal``.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.domain.document_processing.enums import DocumentType
from app.domain.document_processing.exceptions import DocumentProcessingError
from app.domain.document_processing.purchase_order import (
    PurchaseOrderDocument,
    PurchaseOrderItemDocument,
)


def test_document_accepts_different_formats_without_breaking() -> None:
    mercadal = PurchaseOrderDocument(
        order_number="4012234",
        customer_code="CL000168",
        items=(
            PurchaseOrderItemDocument(
                description="VIGA MEDIANA BLANCO PEPIN",
                quantity=20,
                uom="PAQ",
                unit_price=Decimal("192.50"),
                total=Decimal("3850.00"),
            ),
        ),
    )
    jumbo = PurchaseOrderDocument(
        order_number="4000326734",
        customer_name="JUMBO HIGUEY",
        delivery_date=date(2026, 8, 3),
        items=(
            PurchaseOrderItemDocument(description="PAN BURGUESA", quantity=27, pdf_code="123"),
        ),
    )
    hilton = PurchaseOrderDocument(
        order_number="BOLIN 4505261004",
        route_code="PPN001",
        items=(
            PurchaseOrderItemDocument(
                description="GALLETA",
                quantity=12,
                ean="7460966301406",
                units_per_pack=12,
                unit_price=Decimal("119.84"),
                total=Decimal("1438.08"),
            ),
        ),
    )

    assert mercadal.order_number == "4012234"
    assert mercadal.items[0].quantity == 20
    assert mercadal.items[0].unit_price == Decimal("192.50")
    assert jumbo.items[0].pdf_code == "123"
    assert hilton.items[0].ean == "7460966301406"
    assert hilton.items[0].units_per_pack == 12
    assert hilton.document_type is DocumentType.UNKNOWN


def test_quantity_must_be_integer() -> None:
    with pytest.raises(DocumentProcessingError, match="quantity must be an integer"):
        PurchaseOrderItemDocument(description="VIGA", quantity=2.5)

    with pytest.raises(DocumentProcessingError, match="quantity must be greater than zero"):
        PurchaseOrderItemDocument(description="VIGA", quantity=0)


def test_monetary_fields_support_decimal() -> None:
    item = PurchaseOrderItemDocument(
        description="VIGA",
        quantity=20,
        unit_price=Decimal("192.50"),
        total=Decimal("3850.00"),
    )

    assert item.unit_price == Decimal("192.50")
    assert item.total == Decimal("3850.00")


def test_monetary_fields_reject_float() -> None:
    with pytest.raises(DocumentProcessingError, match="unit_price must be a Decimal"):
        PurchaseOrderItemDocument(description="VIGA", quantity=20, unit_price=192.50)


def test_document_requires_order_number() -> None:
    with pytest.raises(DocumentProcessingError, match="Order number must not be blank"):
        PurchaseOrderDocument(order_number="   ")


def test_item_requires_description() -> None:
    with pytest.raises(DocumentProcessingError, match="Item description must not be blank"):
        PurchaseOrderItemDocument(description=" ", quantity=6)


def test_document_traceability_fields() -> None:
    doc = PurchaseOrderDocument(
        order_number="12653",
        customer_code="CL000168",
        customer_name="JASON FAST FOOD",
        route_code="PPN002",
        order_date=date(2026, 8, 3),
        delivery_date=date(2026, 8, 10),
        source_filename="pedido-03-08-2026-12653-bravo.pdf",
        document_type=DocumentType.BRAVO,
    )

    assert doc.customer_name == "JASON FAST FOOD"
    assert doc.source_filename == "pedido-03-08-2026-12653-bravo.pdf"
    assert doc.document_type is DocumentType.BRAVO
