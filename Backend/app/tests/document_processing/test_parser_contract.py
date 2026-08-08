"""Tests for the IPDFParser contract (ADR-002)."""

import pytest

from app.domain.document_processing.models import RawDocumentData
from app.domain.document_processing.purchase_order import (
    PurchaseOrderDocument,
    PurchaseOrderItemDocument,
)
from app.domain.interfaces import IPDFParser


def test_ipdfparser_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        IPDFParser()


def test_concrete_parser_implements_contract() -> None:
    class FakeParser(IPDFParser):
        def parse(self, raw_document: RawDocumentData) -> PurchaseOrderDocument:
            return PurchaseOrderDocument(
                order_number="12653",
                items=(
                    PurchaseOrderItemDocument(description="VIGA MEDIANA", quantity=6),
                ),
            )

    parser = FakeParser()
    result = parser.parse(RawDocumentData(filename="fake.pdf"))

    assert isinstance(result, PurchaseOrderDocument)
    assert result.order_number == "12653"
    assert result.items[0].description == "VIGA MEDIANA"
    assert isinstance(parser, IPDFParser)
