"""Run the full workflow against the definitive catalog (evidence table).

Pipeline for every text-based sample PDF:
    Reader -> Detector -> Parser -> CustomerMatcher -> RouteResolver
    -> OrderValidationService -> OrderRepository.save

The catalog is loaded from the committed source workbook
(``docs/data/CLIENTES POR RUTA.xlsx``) into an in-memory repository, so this
script reproduces production matching without a database.

The 2 scanned PDFs are reported as SCANNED (OCR is a future extension).

Usage:
    python scripts/process_workflow.py
"""

from pathlib import Path

import openpyxl

from app.application.services.order_validation import OrderValidationService
from app.application.services.route_resolution import RouteResolver
from app.application.use_cases import ProcessPurchaseOrder
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

DATA_DIR = Path(__file__).resolve().parents[2] / "docs" / "data"
SAMPLES_DIR = Path(__file__).resolve().parents[2] / "docs" / "samples"


def load_customers(path: Path) -> list[Customer]:
    """Load CLIENTES POR RUTA (route, name, address) into domain customers."""
    routes: dict[str, Route] = {}
    customers: list[Customer] = []
    workbook = openpyxl.load_workbook(path, data_only=True)
    for index, row in enumerate(workbook.active.iter_rows(values_only=True)):
        if index == 0:
            continue
        route_code = str(row[0]).strip() if row[0] is not None else ""
        name = str(row[1]).strip() if row[1] is not None else ""
        if not route_code or not name:
            continue
        if route_code not in routes:
            routes[route_code] = Route(code=route_code, name=route_code)
        address = str(row[2]).strip() if len(row) > 2 and row[2] is not None else None
        customers.append(Customer(name=name, route=routes[route_code], address=address))
    return customers


def build_use_case() -> ProcessPurchaseOrder:
    customers = load_customers(DATA_DIR / "CLIENTES POR RUTA.xlsx")
    return ProcessPurchaseOrder(
        reader=PdfplumberPDFReader(),
        detector=DocumentDetector(signatures=DEFAULT_SIGNATURES),
        registry=ParserRegistry.with_defaults(),
        customer_matcher=CatalogCustomerMatcher(InMemoryCustomerRepository(customers)),
        route_resolver=RouteResolver(),
        validator=OrderValidationService(),
        orders=InMemoryOrderRepository(),
        history=InMemoryProcessingHistoryRepository(),
    )


def summarize_items(items) -> str:
    if not items:
        return "0"
    return str(len(items))


def main() -> None:
    use_case = build_use_case()
    header = (
        f"{'PDF':<45} {'Parser':<18} {'Orden':<11} {'Cliente (resultado)':<28} "
        f"{'Ruta':<8} {'Items':<8} Estado"
    )
    print(header)
    print("-" * len(header))

    for path in sorted(SAMPLES_DIR.glob("*.pdf")):
        result = use_case.execute(path)
        customer = result.customer_match.matched_customer if result.customer_match else None
        customer_label = f"{customer.name}" if customer else (
            f"REVIEW {len(result.customer_match.candidates)} cand"
            if result.customer_match and result.customer_match.candidates
            else result.customer_match.reason if result.customer_match else "-"
        )
        print(
            f"{path.name:<45} {result.parser_id:<18} {(result.order_number or '-'):<11} "
            f"{customer_label:<28} {(result.route.code if result.route else '-'):<8} "
            f"{summarize_items(result.items):<8} {result.status.value}"
        )
        for reason in result.reasons:
            print(f"    -> {reason}")


if __name__ == "__main__":
    main()
