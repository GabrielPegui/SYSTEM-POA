"""Parser tests against the real sample corpus (Sprint 6)."""

from decimal import Decimal

import pytest

from app.domain.document_processing.enums import DocumentType
from app.infrastructure.document_processing.parsers.registry import (
    DEFAULT_PARSERS,
    ParserRegistry,
)

SAMPLES = {
    "OLE(imagen).pdf": "mercadal_parser",
    "mercadal.pdf": "mercadal_parser",
    "OPERADORA WESTPARK, SAS.pdf": "hilton_parser",
    "carrefour.PDF": "cde_hyper_parser",
    "Orden de Pedido por e-mail.pdf": "jumbo_parser",
    "bravo(imagen).pdf": "bravo_parser",
    "plazalama.pdf": "plaza_lama_parser",
}


@pytest.mark.parametrize("filename,parser_id", SAMPLES.items())
def test_pipeline_detects_and_parses_sample(reader, detector, samples_dir, filename, parser_id):
    raw = reader.read(samples_dir / filename)
    detection = detector.detect(raw)
    assert detection.is_recognized
    assert detection.parser_id == parser_id
    document = DEFAULT_PARSERS[parser_id].parse(raw)
    assert document.document_type is detection.document_type
    assert document.document_type != DocumentType.UNKNOWN
    assert document.order_number
    assert document.items
    assert all(item.quantity > 0 for item in document.items)
    assert all(item.description for item in document.items)


def test_mercadal_parses_first_sample(reader, samples_dir):
    raw = reader.read(samples_dir / "OLE(imagen).pdf")
    document = DEFAULT_PARSERS["mercadal_parser"].parse(raw)
    assert document.order_number == "4000326734"
    assert document.customer_code == "101532483"
    assert len(document.items) == 11
    first = document.items[0]
    assert first.pdf_code == "110000002260"
    assert first.quantity == 211
    assert first.unit_price == Decimal("82.00")
    assert first.total == Decimal("17302.00")
    assert first.ean == "7460966301406"
    assert first.description.startswith("PEPIN")
    assert document.items[1].ean == "7460966301246"


def test_mercadal_parses_second_sample(reader, samples_dir):
    raw = reader.read(samples_dir / "mercadal.pdf")
    document = DEFAULT_PARSERS["mercadal_parser"].parse(raw)
    assert document.order_number == "4000326758"
    assert document.customer_code == "131242172"
    assert len(document.items) == 10


def test_hilton_parses_sample(reader, samples_dir):
    raw = reader.read(samples_dir / "OPERADORA WESTPARK, SAS.pdf")
    document = DEFAULT_PARSERS["hilton_parser"].parse(raw)
    assert document.order_number == "4012234"
    assert document.customer_code == "132407083"
    assert len(document.items) == 2
    first = document.items[0]
    assert first.pdf_code == "OWP03000295"
    assert first.quantity == 20
    assert first.unit_price == Decimal("192.50")
    assert first.total == Decimal("3850.00")
    assert first.uom == "PAQ"


def test_cde_hyper_parses_multipage_sample(reader, samples_dir):
    raw = reader.read(samples_dir / "carrefour.PDF")
    assert raw.page_count == 2
    document = DEFAULT_PARSERS["cde_hyper_parser"].parse(raw)
    assert document.order_number == "15070619"
    assert document.customer_code == "101802456"
    assert len(document.items) == 20
    first = document.items[0]
    assert first.pdf_code == "69251"
    assert first.ean == "7460966303011"
    assert first.quantity == 1
    x12 = next(item for item in document.items if item.pdf_code == "14000205")
    assert x12.quantity == 12
    assert x12.unit_price == Decimal("66.700")


def test_jumbo_parses_sample(reader, samples_dir):
    raw = reader.read(samples_dir / "Orden de Pedido por e-mail.pdf")
    document = DEFAULT_PARSERS["jumbo_parser"].parse(raw)
    assert document.order_number == "4117171895"
    assert document.customer_code == "101-01992-1"
    assert len(document.items) == 5
    first = document.items[0]
    assert first.pdf_code == "2005494"
    assert first.ean == "7460966301017"
    assert first.quantity == 27
    assert first.unit_price == Decimal("121.90")
    assert first.total == Decimal("3291.30")
    assert first.line_number == 1


def test_bravo_parses_sample(reader, samples_dir):
    raw = reader.read(samples_dir / "bravo(imagen).pdf")
    document = DEFAULT_PARSERS["bravo_parser"].parse(raw)
    assert document.order_number == "3846637"
    assert len(document.items) == 1
    item = document.items[0]
    assert item.pdf_code == "41296"
    assert item.ean == "7460966303059"
    assert item.quantity == 180
    assert item.unit_price == Decimal("106.35")
    assert item.total == Decimal("19143.00")


def test_plaza_lama_parses_multipage_sample(reader, samples_dir):
    raw = reader.read(samples_dir / "plazalama.pdf")
    assert raw.page_count == 2
    document = DEFAULT_PARSERS["plaza_lama_parser"].parse(raw)
    assert document.order_number == "4505261004"
    assert len(document.items) == 8
    first = document.items[0]
    assert first.quantity == 10
    assert first.unit_price == Decimal("78.40")
    assert first.total == Decimal("784.00")
    assert document.items[-1].line_number == 80


def test_registry_resolves_default_parsers() -> None:
    registry = ParserRegistry(DEFAULT_PARSERS)
    assert "mercadal_parser" in registry
    assert "plaza_lama_parser" in registry
    assert registry.get("mercadal_parser") is DEFAULT_PARSERS["mercadal_parser"]
    assert set(registry.parser_ids) == set(DEFAULT_PARSERS)


def test_registry_unknown_parser_raises() -> None:
    registry = ParserRegistry()
    with pytest.raises(KeyError):
        registry.get("unknown_parser")


def test_registry_with_defaults() -> None:
    registry = ParserRegistry.with_defaults()
    assert "hilton_parser" in registry
    assert registry.get("hilton_parser") is DEFAULT_PARSERS["hilton_parser"]
