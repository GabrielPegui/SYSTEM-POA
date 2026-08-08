"""Tests for the ``POST /orders/process`` endpoint (Sprint 7).

The endpoint returns a uniform ``ProcessOrderResponse`` with a ``status`` of
``processed`` / ``review_required`` / ``no_match`` / ``error``. The use case
is overridden with the real pipeline driven by in-memory fakes so the
transport contract (multipart upload, DTO mapping) is tested in isolation.

Pre-Sprint 8 hardening: non-PDF uploads are rejected with ``415`` and
oversized uploads with ``413`` before reaching the pipeline, and the original
``file.filename`` is preserved as ``source_filename``.
"""

from pathlib import Path

from app.api.deps import get_process_purchase_order
from app.application.services.order_validation import OrderValidationService
from app.application.services.route_resolution import RouteResolver
from app.application.use_cases import ProcessPurchaseOrder
from app.core.config import settings
from app.domain.entities import Customer, Product, Route
from app.infrastructure.document_processing.detector import DocumentDetector
from app.infrastructure.document_processing.parsers.registry import DEFAULT_PARSERS, ParserRegistry
from app.infrastructure.document_processing.reader import PdfplumberPDFReader
from app.infrastructure.document_processing.signatures import DEFAULT_SIGNATURES
from app.infrastructure.matching.catalog_customer_matcher import CatalogCustomerMatcher
from app.infrastructure.matching.catalog_product_matcher import CatalogProductMatcher
from app.tests.application.fakes import (
    InMemoryCustomerRepository,
    InMemoryOrderRepository,
    InMemoryProcessingHistoryRepository,
    InMemoryProductRepository,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
SAMPLES_DIR = REPO_ROOT / "docs" / "samples"


def _build_process_use_case(customers: list[Customer], products: list[Product]) -> ProcessPurchaseOrder:
    reader = PdfplumberPDFReader()
    detector = DocumentDetector(signatures=DEFAULT_SIGNATURES)
    return ProcessPurchaseOrder(
        reader=reader,
        detector=detector,
        registry=ParserRegistry.with_defaults(),
        customer_matcher=CatalogCustomerMatcher(InMemoryCustomerRepository(customers)),
        product_matcher=CatalogProductMatcher(InMemoryProductRepository(products)),
        route_resolver=RouteResolver(),
        validator=OrderValidationService(),
        orders=InMemoryOrderRepository(),
        history=InMemoryProcessingHistoryRepository(),
    )


def _seeded_catalog() -> tuple[list[Customer], list[Product]]:
    reader = PdfplumberPDFReader()
    detector = DocumentDetector(signatures=DEFAULT_SIGNATURES)
    raw = reader.read(SAMPLES_DIR / "4000326758.pdf")
    document = DEFAULT_PARSERS[detector.detect(raw).parser_id].parse(raw)
    customer = Customer(
        code="CL000004-101",
        name="MERCADAL GUARICANO",
        route=Route(code="PPN006", name="Ruta 6"),
        rnc="131242172",
    )
    products = [
        Product(code=item.pdf_code or f"P{index}", description=item.description)
        for index, item in enumerate(document.items)
    ]
    return [customer], products


def test_process_mercadal_returns_processed_dto(client) -> None:
    customers, products = _seeded_catalog()
    client.app.dependency_overrides[get_process_purchase_order] = lambda: _build_process_use_case(
        customers, products
    )

    pdf_bytes = (SAMPLES_DIR / "4000326758.pdf").read_bytes()
    response = client.post(
        "/orders/process",
        files={"file": ("4000326758.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["parser_id"] == "mercadal_parser"
    assert body["order_number"] == "4000326758"
    assert body["customer_code"] == "CL000004-101"
    assert body["customer_name"] == "MERCADAL GUARICANO"
    assert body["route_code"] == "PPN006"
    assert body["reasons"] == []
    assert "processed_at" in body
    assert len(body["items"]) == 10
    assert body["items"][0]["match_status"] == "matched"
    assert body["items"][0]["product_code"] is not None


def test_process_preserves_original_filename(client) -> None:
    customers, products = _seeded_catalog()
    client.app.dependency_overrides[get_process_purchase_order] = lambda: _build_process_use_case(
        customers, products
    )

    pdf_bytes = (SAMPLES_DIR / "4000326758.pdf").read_bytes()
    response = client.post(
        "/orders/process",
        files={"file": ("Orden 123.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source_filename"] == "Orden 123.pdf"
    assert body["status"] == "processed"


def test_process_preserves_filename_with_directories(client) -> None:
    customers, products = _seeded_catalog()
    client.app.dependency_overrides[get_process_purchase_order] = lambda: _build_process_use_case(
        customers, products
    )

    pdf_bytes = (SAMPLES_DIR / "4000326758.pdf").read_bytes()
    response = client.post(
        "/orders/process",
        files={"file": (r"C:\fake\path\Orden 123.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json()["source_filename"] == "Orden 123.pdf"


def test_process_non_pdf_is_rejected(client) -> None:
    client.app.dependency_overrides[get_process_purchase_order] = lambda: _build_process_use_case([], [])

    response = client.post(
        "/orders/process",
        files={"file": ("broken.txt", b"this is not a pdf", "text/plain")},
    )

    assert response.status_code == 415
    body = response.json()
    assert "not a PDF" in body["detail"]


def test_process_corrupt_pdf_with_magic_returns_error_dto(client) -> None:
    client.app.dependency_overrides[get_process_purchase_order] = lambda: _build_process_use_case([], [])

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
    client.app.dependency_overrides[get_process_purchase_order] = lambda: _build_process_use_case([], [])
    monkeypatch.setattr(settings, "max_upload_mb", 1)

    response = client.post(
        "/orders/process",
        files={"file": ("big.pdf", b"%PDF-1.4" + b"x" * (1024 * 1024 + 10), "application/pdf")},
    )

    assert response.status_code == 413
    body = response.json()
    assert "maximum allowed size" in body["detail"]
