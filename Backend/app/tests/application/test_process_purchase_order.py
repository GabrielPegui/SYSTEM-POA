"""End-to-end tests for the ProcessPurchaseOrder use case.

The use case runs the real PDF pipeline (reader, detector, registry, parsers)
against the committed sample corpus and drives matching, route resolution and
validation through in-memory fakes. The customer catalog is seeded so the
tests are deterministic:

- ``mercadal.pdf``: name matches a single catalog customer -> PROCESSED and
  persisted.
- ``4000326734.pdf``/ambiguous name: the extracted name maps to more than one
  catalog customer -> REVIEW_REQUIRED, nothing persisted.
- Unknown name -> NO_MATCH, nothing persisted.
- Unreadable file -> ERROR, nothing persisted.

Every attempt is also recorded in ``ProcessingHistory``; only PROCESSED
creates an Order.
"""

from pathlib import Path

import pytest

from app.application.services.order_validation import OrderValidationService
from app.application.services.route_resolution import RouteResolver
from app.application.use_cases import ProcessPurchaseOrder
from app.domain.document_processing.processing import ProcessingStatus
from app.domain.entities import Customer, Route
from app.domain.exceptions import CatalogReferenceNotFoundError
from app.infrastructure.document_processing.detector import DocumentDetector
from app.infrastructure.document_processing.parsers.registry import ParserRegistry
from app.infrastructure.document_processing.reader import PdfplumberPDFReader
from app.infrastructure.document_processing.signatures import DEFAULT_SIGNATURES
from app.infrastructure.matching.catalog_customer_matcher import CatalogCustomerMatcher
from app.tests.application.fakes import (
    FailingOrderRepository,
    InMemoryCustomerRepository,
    InMemoryOrderRepository,
    InMemoryProcessingHistoryRepository,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
SAMPLES_DIR = REPO_ROOT / "docs" / "samples"

ROUTE_6 = Route(code="PPN006", name="Ruta 6")
ROUTE_2 = Route(code="PPN002", name="Ruta 2")


def _use_case(
    customers: list[Customer],
    orders: InMemoryOrderRepository | None = None,
    history: InMemoryProcessingHistoryRepository | None = None,
) -> ProcessPurchaseOrder:
    return ProcessPurchaseOrder(
        reader=PdfplumberPDFReader(),
        detector=DocumentDetector(signatures=DEFAULT_SIGNATURES),
        registry=ParserRegistry.with_defaults(),
        customer_matcher=CatalogCustomerMatcher(InMemoryCustomerRepository(customers)),
        route_resolver=RouteResolver(),
        validator=OrderValidationService(),
        orders=orders or InMemoryOrderRepository(),
        history=history or InMemoryProcessingHistoryRepository(),
    )


def _mercadal() -> Customer:
    return Customer(
        name="MERCADAL GUARICANO",
        route=ROUTE_6,
        address="Sector Guaicanos",
    )


def test_processes_unique_mercadal_order_and_persists() -> None:
    orders = InMemoryOrderRepository()
    use_case = _use_case(customers=[_mercadal()], orders=orders)

    result = use_case.execute(SAMPLES_DIR / "mercadal.pdf")

    assert result.status is ProcessingStatus.PROCESSED
    assert result.parser_id == "mercadal_parser"
    assert result.order_number == "4000326758"
    assert result.customer_match is not None
    assert result.customer_match.matched_customer == _mercadal()
    assert result.route == ROUTE_6
    assert result.customer_code == "131242172"
    assert len(result.items) == 10
    assert result.order is not None
    assert result.order.customer == _mercadal()
    assert result.order.delivery_date is not None
    assert len(orders.list()) == 1
    assert orders.list()[0].order_number == "4000326758"


def test_ambiguous_customer_name_requires_review_and_is_not_persisted() -> None:
    duplicated = [
        Customer(name="MERCADAL GUARICANO", route=ROUTE_6),
        Customer(name="MERCADAL GUARICANO", route=ROUTE_2),
    ]
    orders = InMemoryOrderRepository()
    use_case = _use_case(customers=duplicated, orders=orders)

    result = use_case.execute(SAMPLES_DIR / "mercadal.pdf")

    assert result.status is ProcessingStatus.REVIEW_REQUIRED
    assert result.order is None
    assert result.customer_match is not None
    assert len(result.customer_match.candidates) == 2
    assert orders.list() == []


def test_unknown_customer_name_is_no_match_and_is_not_persisted() -> None:
    orders = InMemoryOrderRepository()
    use_case = _use_case(
        customers=[Customer(name="JUMBO HIGUEY", route=ROUTE_2)],
        orders=orders,
    )

    result = use_case.execute(SAMPLES_DIR / "mercadal.pdf")

    assert result.status is ProcessingStatus.NO_MATCH
    assert result.order is None
    assert orders.list() == []


def test_missing_catalog_reference_is_reported_as_error() -> None:
    failing = FailingOrderRepository(CatalogReferenceNotFoundError("Route", "PPN006"))
    use_case = _use_case(customers=[_mercadal()], orders=failing)

    result = use_case.execute(SAMPLES_DIR / "mercadal.pdf")

    assert result.status is ProcessingStatus.ERROR
    assert result.order is None


def test_unexpected_persistence_error_propagates() -> None:
    failing = FailingOrderRepository(RuntimeError("database unavailable"))
    use_case = _use_case(customers=[_mercadal()], orders=failing)

    with pytest.raises(RuntimeError, match="database unavailable"):
        use_case.execute(SAMPLES_DIR / "mercadal.pdf")


def test_unreadable_file_is_reported_as_error(tmp_path: Path) -> None:
    bad_file = tmp_path / "broken.pdf"
    bad_file.write_bytes(b"this is not a pdf")

    use_case = _use_case(customers=[])
    result = use_case.execute(bad_file)

    assert result.status is ProcessingStatus.ERROR
    assert result.parser_id == "unknown"
    assert result.order is None


def test_processed_attempt_is_recorded_in_history() -> None:
    history = InMemoryProcessingHistoryRepository()
    use_case = _use_case(customers=[_mercadal()], history=history)

    result = use_case.execute(SAMPLES_DIR / "mercadal.pdf")

    assert result.status is ProcessingStatus.PROCESSED
    records = history.list()
    assert len(records) == 1
    record = records[0]
    assert record.status is ProcessingStatus.PROCESSED
    assert record.source_filename == "mercadal.pdf"
    assert record.order_number == "4000326758"
    assert record.parser_id == "mercadal_parser"
    assert record.customer_code == "131242172"
    assert record.customer_name == "MERCADAL GUARICANO"
    assert record.route_code == "PPN006"
    assert record.item_count == 10


def test_review_required_attempt_is_recorded_without_order() -> None:
    duplicated = [
        Customer(name="MERCADAL GUARICANO", route=ROUTE_6),
        Customer(name="MERCADAL GUARICANO", route=ROUTE_2),
    ]
    orders = InMemoryOrderRepository()
    history = InMemoryProcessingHistoryRepository()
    use_case = _use_case(customers=duplicated, orders=orders, history=history)

    result = use_case.execute(SAMPLES_DIR / "mercadal.pdf")

    assert result.status is ProcessingStatus.REVIEW_REQUIRED
    assert orders.list() == []
    records = history.list()
    assert len(records) == 1
    assert records[0].status is ProcessingStatus.REVIEW_REQUIRED
    assert records[0].reasons


def test_no_match_attempt_is_recorded_without_order() -> None:
    orders = InMemoryOrderRepository()
    history = InMemoryProcessingHistoryRepository()
    use_case = _use_case(
        customers=[Customer(name="JUMBO HIGUEY", route=ROUTE_2)],
        orders=orders,
        history=history,
    )

    result = use_case.execute(SAMPLES_DIR / "mercadal.pdf")

    assert result.status is ProcessingStatus.NO_MATCH
    assert orders.list() == []
    records = history.list()
    assert len(records) == 1
    assert records[0].status is ProcessingStatus.NO_MATCH


def test_error_attempt_is_recorded_in_history(tmp_path: Path) -> None:
    bad_file = tmp_path / "broken.pdf"
    bad_file.write_bytes(b"this is not a pdf")
    history = InMemoryProcessingHistoryRepository()
    use_case = _use_case(customers=[], history=history)

    result = use_case.execute(bad_file)

    assert result.status is ProcessingStatus.ERROR
    records = history.list()
    assert len(records) == 1
    assert records[0].status is ProcessingStatus.ERROR
    assert records[0].source_filename == "broken.pdf"
    assert records[0].reasons


def test_order_save_failure_is_recorded_as_error_in_history() -> None:
    failing = FailingOrderRepository(CatalogReferenceNotFoundError("Route", "PPN006"))
    history = InMemoryProcessingHistoryRepository()
    use_case = _use_case(customers=[_mercadal()], orders=failing, history=history)

    result = use_case.execute(SAMPLES_DIR / "mercadal.pdf")

    assert result.status is ProcessingStatus.ERROR
    assert result.order is None
    records = history.list()
    assert len(records) == 1
    assert records[0].status is ProcessingStatus.ERROR
    assert "catalog reference missing" in records[0].reasons[0]


def test_history_save_failure_propagates() -> None:
    """A history persistence failure propagates like an unexpected DB error."""

    class ExplodingHistory(InMemoryProcessingHistoryRepository):
        def save(self, record):
            raise RuntimeError("history database unavailable")

    use_case = _use_case(customers=[_mercadal()], history=ExplodingHistory())

    with pytest.raises(RuntimeError, match="history database unavailable"):
        use_case.execute(SAMPLES_DIR / "mercadal.pdf")
