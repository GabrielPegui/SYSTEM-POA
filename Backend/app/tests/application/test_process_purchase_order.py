"""End-to-end tests for the ProcessPurchaseOrder use case (Sprint 7).

The use case runs the real PDF pipeline (reader, detector, registry, parsers)
against the committed sample corpus and drives matching, route resolution and
validation through in-memory fakes. The catalog is seeded so the tests are
deterministic:

- ``4000326758.pdf``: unique RNC -> PROCESSED and persisted.
- ``4000326734.pdf``: shared RNC -> REVIEW_REQUIRED, nothing persisted.
- Empty product catalog -> NO_MATCH, nothing persisted.
- Unreadable file -> ERROR, nothing persisted.

Pre-Sprint 8.1 (Objective B): every attempt is also recorded in
``ProcessingHistory``; only PROCESSED creates an Order.
"""

from pathlib import Path

import pytest

from app.application.services.order_validation import OrderValidationService
from app.application.services.route_resolution import RouteResolver
from app.application.use_cases import ProcessPurchaseOrder
from app.domain.document_processing.processing import ProcessingStatus
from app.domain.entities import Customer, Product, Route
from app.domain.exceptions import CatalogReferenceNotFoundError
from app.infrastructure.document_processing.detector import DocumentDetector
from app.infrastructure.document_processing.parsers.registry import DEFAULT_PARSERS, ParserRegistry
from app.infrastructure.document_processing.reader import PdfplumberPDFReader
from app.infrastructure.document_processing.signatures import DEFAULT_SIGNATURES
from app.infrastructure.matching.catalog_customer_matcher import CatalogCustomerMatcher
from app.infrastructure.matching.catalog_product_matcher import CatalogProductMatcher
from app.tests.application.fakes import (
    FailingOrderRepository,
    InMemoryCustomerRepository,
    InMemoryOrderRepository,
    InMemoryProcessingHistoryRepository,
    InMemoryProductRepository,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
SAMPLES_DIR = REPO_ROOT / "docs" / "samples"

ROUTE_6 = Route(code="PPN006", name="Ruta 6")
ROUTE_1 = Route(code="PPN001", name="Ruta 1")
ROUTE_2 = Route(code="PPN002", name="Ruta 2")


def _read_and_parse(filename: str):
    reader = PdfplumberPDFReader()
    detector = DocumentDetector(signatures=DEFAULT_SIGNATURES)
    raw = reader.read(SAMPLES_DIR / filename)
    detection = detector.detect(raw)
    document = DEFAULT_PARSERS[detection.parser_id].parse(raw)
    return reader, detector, detection, document


def _products_for(document) -> list[Product]:
    return [
        Product(code=item.pdf_code or f"P{index}", description=item.description)
        for index, item in enumerate(document.items)
    ]


def _use_case(
    customers: list[Customer],
    products: list[Product],
    orders: InMemoryOrderRepository | None = None,
    history: InMemoryProcessingHistoryRepository | None = None,
) -> ProcessPurchaseOrder:
    reader, detector, _, _ = _read_and_parse("4000326758.pdf")
    return ProcessPurchaseOrder(
        reader=reader,
        detector=detector,
        registry=ParserRegistry.with_defaults(),
        customer_matcher=CatalogCustomerMatcher(InMemoryCustomerRepository(customers)),
        product_matcher=CatalogProductMatcher(InMemoryProductRepository(products)),
        route_resolver=RouteResolver(),
        validator=OrderValidationService(),
        orders=orders or InMemoryOrderRepository(),
        history=history or InMemoryProcessingHistoryRepository(),
    )


def test_processes_unique_mercadal_order_and_persists() -> None:
    _, _, _, document = _read_and_parse("4000326758.pdf")
    customer = Customer(
        code="CL000004-101",
        name="MERCADAL GUARICANO",
        route=ROUTE_6,
        rnc="131242172",
    )
    orders = InMemoryOrderRepository()
    use_case = _use_case(customers=[customer], products=_products_for(document), orders=orders)

    result = use_case.execute(SAMPLES_DIR / "4000326758.pdf")

    assert result.status is ProcessingStatus.PROCESSED
    assert result.parser_id == "mercadal_parser"
    assert result.order_number == "4000326758"
    assert result.customer_match is not None
    assert result.customer_match.matched_customer == customer
    assert result.route == ROUTE_6
    assert len(result.items) == len(document.items)
    assert result.order is not None
    assert result.order.customer == customer
    assert result.order.delivery_date == document.delivery_date
    assert len(orders.list()) == 1
    assert orders.list()[0].order_number == "4000326758"


def test_shared_rnc_requires_review_and_is_not_persisted() -> None:
    _, _, _, document = _read_and_parse("4000326734.pdf")
    customers = [
        Customer(code="CL000001-001", name="MERCADAL AV DUARTE", route=ROUTE_2, rnc="101532483"),
        Customer(code="CL000001-002", name="MERCADAL AUTOPISTA", route=ROUTE_1, rnc="101532483"),
    ]
    orders = InMemoryOrderRepository()
    use_case = _use_case(customers=customers, products=_products_for(document), orders=orders)

    result = use_case.execute(SAMPLES_DIR / "4000326734.pdf")

    assert result.status is ProcessingStatus.REVIEW_REQUIRED
    assert result.order is None
    assert result.customer_match is not None
    assert len(result.customer_match.candidates) == 2
    assert orders.list() == []


def test_empty_product_catalog_is_no_match_and_is_not_persisted() -> None:
    customer = Customer(
        code="CL000004-101",
        name="MERCADAL GUARICANO",
        route=ROUTE_6,
        rnc="131242172",
    )
    orders = InMemoryOrderRepository()
    use_case = _use_case(customers=[customer], products=[], orders=orders)

    result = use_case.execute(SAMPLES_DIR / "4000326758.pdf")

    assert result.status is ProcessingStatus.NO_MATCH
    assert result.order is None
    assert orders.list() == []


def test_missing_catalog_reference_is_reported_as_error() -> None:
    _, _, _, document = _read_and_parse("4000326758.pdf")
    customer = Customer(
        code="CL000004-101",
        name="MERCADAL GUARICANO",
        route=ROUTE_6,
        rnc="131242172",
    )
    failing = FailingOrderRepository(CatalogReferenceNotFoundError("Route", "PPN006"))
    use_case = _use_case(customers=[customer], products=_products_for(document), orders=failing)

    result = use_case.execute(SAMPLES_DIR / "4000326758.pdf")

    assert result.status is ProcessingStatus.ERROR
    assert result.order is None


def test_unexpected_persistence_error_propagates() -> None:
    _, _, _, document = _read_and_parse("4000326758.pdf")
    customer = Customer(
        code="CL000004-101",
        name="MERCADAL GUARICANO",
        route=ROUTE_6,
        rnc="131242172",
    )
    failing = FailingOrderRepository(RuntimeError("database unavailable"))
    use_case = _use_case(customers=[customer], products=_products_for(document), orders=failing)

    with pytest.raises(RuntimeError, match="database unavailable"):
        use_case.execute(SAMPLES_DIR / "4000326758.pdf")


def test_unreadable_file_is_reported_as_error(tmp_path: Path) -> None:
    bad_file = tmp_path / "broken.pdf"
    bad_file.write_bytes(b"this is not a pdf")

    use_case = _use_case(customers=[], products=[])
    result = use_case.execute(bad_file)

    assert result.status is ProcessingStatus.ERROR
    assert result.parser_id == "unknown"
    assert result.order is None


def test_processed_attempt_is_recorded_in_history() -> None:
    _, _, _, document = _read_and_parse("4000326758.pdf")
    customer = Customer(
        code="CL000004-101",
        name="MERCADAL GUARICANO",
        route=ROUTE_6,
        rnc="131242172",
    )
    history = InMemoryProcessingHistoryRepository()
    use_case = _use_case(customers=[customer], products=_products_for(document), history=history)

    result = use_case.execute(SAMPLES_DIR / "4000326758.pdf")

    assert result.status is ProcessingStatus.PROCESSED
    records = history.list()
    assert len(records) == 1
    record = records[0]
    assert record.status is ProcessingStatus.PROCESSED
    assert record.source_filename == "4000326758.pdf"
    assert record.order_number == "4000326758"
    assert record.parser_id == "mercadal_parser"
    assert record.customer_code == "CL000004-101"
    assert record.customer_name == "MERCADAL GUARICANO"
    assert record.route_code == "PPN006"
    assert record.item_count == len(document.items)


def test_review_required_attempt_is_recorded_without_order() -> None:
    _, _, _, document = _read_and_parse("4000326734.pdf")
    customers = [
        Customer(code="CL000001-001", name="MERCADAL AV DUARTE", route=ROUTE_2, rnc="101532483"),
        Customer(code="CL000001-002", name="MERCADAL AUTOPISTA", route=ROUTE_1, rnc="101532483"),
    ]
    orders = InMemoryOrderRepository()
    history = InMemoryProcessingHistoryRepository()
    use_case = _use_case(customers=customers, products=_products_for(document), orders=orders, history=history)

    result = use_case.execute(SAMPLES_DIR / "4000326734.pdf")

    assert result.status is ProcessingStatus.REVIEW_REQUIRED
    assert orders.list() == []
    records = history.list()
    assert len(records) == 1
    assert records[0].status is ProcessingStatus.REVIEW_REQUIRED
    assert records[0].reasons


def test_no_match_attempt_is_recorded_without_order() -> None:
    customer = Customer(
        code="CL000004-101",
        name="MERCADAL GUARICANO",
        route=ROUTE_6,
        rnc="131242172",
    )
    orders = InMemoryOrderRepository()
    history = InMemoryProcessingHistoryRepository()
    use_case = _use_case(customers=[customer], products=[], orders=orders, history=history)

    result = use_case.execute(SAMPLES_DIR / "4000326758.pdf")

    assert result.status is ProcessingStatus.NO_MATCH
    assert orders.list() == []
    records = history.list()
    assert len(records) == 1
    assert records[0].status is ProcessingStatus.NO_MATCH


def test_error_attempt_is_recorded_in_history(tmp_path: Path) -> None:
    bad_file = tmp_path / "broken.pdf"
    bad_file.write_bytes(b"this is not a pdf")
    history = InMemoryProcessingHistoryRepository()
    use_case = _use_case(customers=[], products=[], history=history)

    result = use_case.execute(bad_file)

    assert result.status is ProcessingStatus.ERROR
    records = history.list()
    assert len(records) == 1
    assert records[0].status is ProcessingStatus.ERROR
    assert records[0].source_filename == "broken.pdf"
    assert records[0].reasons


def test_order_save_failure_is_recorded_as_error_in_history() -> None:
    _, _, _, document = _read_and_parse("4000326758.pdf")
    customer = Customer(
        code="CL000004-101",
        name="MERCADAL GUARICANO",
        route=ROUTE_6,
        rnc="131242172",
    )
    failing = FailingOrderRepository(CatalogReferenceNotFoundError("Route", "PPN006"))
    history = InMemoryProcessingHistoryRepository()
    use_case = _use_case(
        customers=[customer],
        products=_products_for(document),
        orders=failing,
        history=history,
    )

    result = use_case.execute(SAMPLES_DIR / "4000326758.pdf")

    assert result.status is ProcessingStatus.ERROR
    assert result.order is None
    records = history.list()
    assert len(records) == 1
    assert records[0].status is ProcessingStatus.ERROR
    assert "catalog reference missing" in records[0].reasons[0]


def test_history_save_failure_propagates() -> None:
    """A history persistence failure propagates like an unexpected DB error."""
    _, _, _, document = _read_and_parse("4000326758.pdf")
    customer = Customer(
        code="CL000004-101",
        name="MERCADAL GUARICANO",
        route=ROUTE_6,
        rnc="131242172",
    )

    class ExplodingHistory(InMemoryProcessingHistoryRepository):
        def save(self, record):
            raise RuntimeError("history database unavailable")

    use_case = _use_case(
        customers=[customer],
        products=_products_for(document),
        history=ExplodingHistory(),
    )

    with pytest.raises(RuntimeError, match="history database unavailable"):
        use_case.execute(SAMPLES_DIR / "4000326758.pdf")
