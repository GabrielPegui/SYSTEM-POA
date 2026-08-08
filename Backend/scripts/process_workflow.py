"""Run the full Sprint 7 workflow against the real catalogs (evidence table).

Pipeline for every text-based sample PDF:
    Reader -> Detector -> Parser -> CustomerMatcher -> RouteResolver
    -> ProductMatcher -> OrderValidationService -> OrderRepository.save

The catalogs are loaded from the committed source data (``docs/data``) into
in-memory repositories, so this script reproduces production matching against
the real ``OUT_CLIENTES`` / ``OUT_PRODUCTO`` without a database.

The 2 scanned PDFs are reported as SCANNED (OCR is a future extension).

Usage:
    python scripts/process_workflow.py
"""

import csv
from pathlib import Path

from app.application.services.order_validation import OrderValidationService
from app.application.services.route_resolution import RouteResolver
from app.application.use_cases import ProcessPurchaseOrder
from app.domain.entities import Customer, Product, Route
from app.infrastructure.document_processing.detector import DocumentDetector
from app.infrastructure.document_processing.parsers.registry import ParserRegistry
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

DATA_DIR = Path(__file__).resolve().parents[2] / "docs" / "data"
SAMPLES_DIR = Path(__file__).resolve().parents[2] / "docs" / "samples"


def load_customers(path: Path) -> list[Customer]:
    """Load OUT_CLIENTES (route, code, rnc, name) into domain customers."""
    routes: dict[str, Route] = {}
    customers: dict[str, Customer] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.reader(handle):
            if len(row) < 4 or not row[1]:
                continue
            route_code = row[0]
            if route_code not in routes:
                routes[route_code] = Route(code=route_code, name=route_code)
            rnc = row[2].strip() or None
            code = row[1].strip()
            name = row[3].strip()
            if code and code not in customers:
                customers[code] = Customer(code=code, name=name, route=routes[route_code], rnc=rnc)
    return list(customers.values())


def load_products(path: Path) -> list[Product]:
    """Load OUT_PRODUCTO (code, description) deduplicated by code."""
    products: dict[str, Product] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.reader(handle):
            if len(row) < 3 or not row[1]:
                continue
            code = row[1].strip()
            description = row[2].strip()
            if code and code not in products:
                products[code] = Product(code=code, description=description)
    return list(products.values())


def build_use_case() -> ProcessPurchaseOrder:
    customers = load_customers(DATA_DIR / "OUT_CLIENTES.csv")
    products = load_products(DATA_DIR / "OUT_PRODUCTO.xlsx.csv")
    return ProcessPurchaseOrder(
        reader=PdfplumberPDFReader(),
        detector=DocumentDetector(signatures=DEFAULT_SIGNATURES),
        registry=ParserRegistry.with_defaults(),
        customer_matcher=CatalogCustomerMatcher(InMemoryCustomerRepository(customers)),
        product_matcher=CatalogProductMatcher(InMemoryProductRepository(products)),
        route_resolver=RouteResolver(),
        validator=OrderValidationService(),
        orders=InMemoryOrderRepository(),
        history=InMemoryProcessingHistoryRepository(),
    )


def summarize_items(items) -> str:
    counts: dict[str, int] = {}
    for result in items:
        counts[result.match.outcome.value] = counts.get(result.match.outcome.value, 0) + 1
    return " ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "-"


def main() -> None:
    use_case = build_use_case()
    header = (
        f"{'PDF':<45} {'Parser':<18} {'Orden':<11} {'Cliente (resultado)':<28} "
        f"{'Ruta':<8} {'Items':<24} Estado"
    )
    print(header)
    print("-" * len(header))

    for path in sorted(SAMPLES_DIR.glob("*.pdf")):
        result = use_case.execute(path)
        customer = result.customer_match.matched_customer if result.customer_match else None
        customer_label = f"{customer.code} {customer.name}" if customer else (
            f"REVIEW {len(result.customer_match.candidates)} cand"
            if result.customer_match and result.customer_match.candidates
            else result.customer_match.reason if result.customer_match else "-"
        )
        print(
            f"{path.name:<45} {result.parser_id:<18} {(result.order_number or '-'):<11} "
            f"{customer_label:<28} {(result.route.code if result.route else '-'):<8} "
            f"{summarize_items(result.items):<24} {result.status.value}"
        )
        for reason in result.reasons:
            print(f"    -> {reason}")


if __name__ == "__main__":
    main()
