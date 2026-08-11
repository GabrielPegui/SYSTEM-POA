"""Tests for the ``POST /orders/process`` endpoint.

The endpoint returns a uniform ``ProcessOrderResponse`` with a ``status`` of
``processed`` / ``review_required`` / ``no_match`` / ``error``. The use case
is overridden with the real pipeline driven by in-memory fakes so the
transport contract (multipart upload, DTO mapping) is tested in isolation.

Hardening: non-PDF uploads are rejected with ``415`` and oversized uploads
with ``413`` before reaching the pipeline, and the original ``file.filename``
is preserved as ``source_filename``.
"""

from pathlib import Path

from app.api.deps import get_process_purchase_order
from app.application.services.order_validation import OrderValidationService
from app.application.services.route_resolution import RouteResolver
from app.application.use_cases import ProcessPurchaseOrder
from app.core.config import settings
from app.domain.entities import Customer, Route
from app.infrastructure.document_processing.detector import DocumentDetector
from app.infrastructure.document_processing.parsers.registry import ParserRegistry
from app.infrastructure.document_processing.reader import PdfplumberPDFReader
from app.infrastructure.document_processing.signatures import DEFAULT_SIGNATURES
from app.infrastructure.matching.catalog_customer_matcher import CatalogCustomerMatcher
from app.tests.application.fakes import (
    InMemoryCustomerRepository,
    InMemoryOrderRepository,
    InMemoryProcessingHistoryRepository,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
SAMPLES_DIR = REPO_ROOT / "docs" / "samples"


def _build_process_use_case(customers: list[Customer]) -> ProcessPurchaseOrder:
    reader = PdfplumberPDFReader()
    detector = DocumentDetector(signatures=DEFAULT_SIGNATURES)
    return ProcessPurchaseOrder(
        reader=reader,
        detector=detector,
        registry=ParserRegistry.with_defaults(),
        customer_matcher=CatalogCustomerMatcher(InMemoryCustomerRepository(customers)),
        route_resolver=RouteResolver(),
        validator=OrderValidationService(),
        orders=InMemoryOrderRepository(),
        history=InMemoryProcessingHistoryRepository(),
    )


def _seeded_customers() -> list[Customer]:
    return [
        Customer(
            name="MERCADAL GUARICANO",
            route=Route(code="PPN006", name="Ruta 6"),
            address="Sector Guaicanos",
        )
    ]


def test_process_mercadal_returns_processed_dto(client) -> None:
    client.app.dependency_overrides[get_process_purchase_order] = lambda: _build_process_use_case(
        _seeded_customers()
    )

    pdf_bytes = (SAMPLES_DIR / "mercadal.pdf").read_bytes()
    response = client.post(
        "/orders/process",
        files={"file": ("mercadal.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["parser_id"] == "mercadal_parser"
    assert body["order_number"] == "4000326758"
    assert body["customer_code"] == "131242172"
    assert body["customer_name"] == "MERCADAL GUARICANO"
    assert body["route_code"] == "PPN006"
    assert body["reasons"] == []
    assert "processed_at" in body
    assert len(body["items"]) == 10
    assert body["items"][0]["description"]
    assert body["items"][0]["quantity"] > 0


def test_process_preserves_original_filename(client) -> None:
    client.app.dependency_overrides[get_process_purchase_order] = lambda: _build_process_use_case(
        _seeded_customers()
    )

    pdf_bytes = (SAMPLES_DIR / "mercadal.pdf").read_bytes()
    response = client.post(
        "/orders/process",
        files={"file": ("Orden 123.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source_filename"] == "Orden 123.pdf"
    assert body["status"] == "processed"


def test_process_preserves_filename_with_directories(client) -> None:
    client.app.dependency_overrides[get_process_purchase_order] = lambda: _build_process_use_case(
        _seeded_customers()
    )

    pdf_bytes = (SAMPLES_DIR / "mercadal.pdf").read_bytes()
    response = client.post(
        "/orders/process",
        files={"file": (r"C:\fake\path\Orden 123.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json()["source_filename"] == "Orden 123.pdf"


def test_process_hilton_document_matches_westpark_account(client) -> None:
    client.app.dependency_overrides[get_process_purchase_order] = lambda: _build_process_use_case(
        [
            Customer(
                name="OPERADORA WESTPARK, SAS",
                route=Route(code="PPN001", name="Ruta 1"),
                address="AV TIRADENTE #32 PLAZA",
            )
        ]
    )

    pdf_bytes = (SAMPLES_DIR / "BOLIN 4012234.pdf").read_bytes()
    response = client.post(
        "/orders/process",
        files={"file": ("BOLIN 4012234.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["parser_id"] == "hilton_parser"
    assert body["customer_name"] == "OPERADORA WESTPARK, SAS"
    assert body["route_code"] == "PPN001"


def test_process_non_pdf_is_rejected(client) -> None:
    client.app.dependency_overrides[get_process_purchase_order] = lambda: _build_process_use_case([])

    response = client.post(
        "/orders/process",
        files={"file": ("broken.txt", b"this is not a pdf", "text/plain")},
    )

    assert response.status_code == 415
    body = response.json()
    assert "not a PDF" in body["detail"]


def test_process_corrupt_pdf_with_magic_returns_error_dto(client) -> None:
    client.app.dependency_overrides[get_process_purchase_order] = lambda: _build_process_use_case([])

    response = client.post(
        "/orders/process",
        files={"file": ("broken.pdf", b"%PDF-1.4 not really a pdf", "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert body["parser_id"] == "unknown"
    assert body["reasons"]


def test_process_oversized_file_is_rejected(client, monkeypatch) -> None:
    client.app.dependency_overrides[get_process_purchase_order] = lambda: _build_process_use_case([])
    monkeypatch.setattr(settings, "max_upload_mb", 1)

    response = client.post(
        "/orders/process",
        files={"file": ("big.pdf", b"%PDF-1.4" + b"x" * (1024 * 1024 + 10), "application/pdf")},
    )

    assert response.status_code == 413
    body = response.json()
    assert "maximum allowed size" in body["detail"]
