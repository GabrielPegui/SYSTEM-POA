"""Shared FastAPI dependencies (dependency injection entry points).

Providers wire the concrete SQLAlchemy repositories and the application use
cases. They are the seams that API tests override with in-memory fakes so
the endpoints can be exercised without a SQL Server instance.
"""

from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.application.services import OrderValidationService, RouteResolver
from app.application.use_cases import (
    CreateOrder,
    GetOrder,
    ListOrders,
    ProcessPurchaseOrder,
    ValidateOrder,
)
from app.database.session import get_db
from app.infrastructure.document_processing.detector import DocumentDetector
from app.infrastructure.document_processing.parsers.registry import ParserRegistry
from app.infrastructure.document_processing.reader import PdfplumberPDFReader
from app.infrastructure.document_processing.signatures import DEFAULT_SIGNATURES
from app.infrastructure.matching.catalog_customer_matcher import CatalogCustomerMatcher
from app.infrastructure.repositories import (
    SqlAlchemyCustomerRepository,
    SqlAlchemyOrderRepository,
    SqlAlchemyProcessingHistoryRepository,
    SqlAlchemyRouteRepository,
)

DbSession = Annotated[Session | None, Depends(get_db)]

_reader = PdfplumberPDFReader()
_detector = DocumentDetector(signatures=DEFAULT_SIGNATURES)
_registry = ParserRegistry.with_defaults()


def _require_session(db: Session | None) -> Session:
    if db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")
    return db


def get_route_repository(db: DbSession):
    """Provide the route repository bound to the request session."""
    return SqlAlchemyRouteRepository(_require_session(db))


def get_customer_repository(db: DbSession):
    """Provide the customer repository bound to the request session."""
    return SqlAlchemyCustomerRepository(_require_session(db))


def get_order_repository(db: DbSession):
    """Provide the order repository bound to the request session."""
    return SqlAlchemyOrderRepository(_require_session(db))


def get_processing_history_repository(db: DbSession):
    """Provide the processing history repository bound to the request session."""
    return SqlAlchemyProcessingHistoryRepository(_require_session(db))


def get_create_order(
    customers=Depends(get_customer_repository),
    orders=Depends(get_order_repository),
) -> CreateOrder:
    """Provide the CreateOrder use case."""
    return CreateOrder(customers, orders)


def get_get_order(orders=Depends(get_order_repository)) -> GetOrder:
    """Provide the GetOrder use case."""
    return GetOrder(orders)


def get_list_orders(orders=Depends(get_order_repository)) -> ListOrders:
    """Provide the ListOrders use case."""
    return ListOrders(orders)


def get_validate_order(orders=Depends(get_order_repository)) -> ValidateOrder:
    """Provide the ValidateOrder use case."""
    return ValidateOrder(orders)


def get_reader() -> PdfplumberPDFReader:
    """Provide the PDF reader (stateless singleton)."""
    return _reader


def get_detector() -> DocumentDetector:
    """Provide the document detector (stateless singleton)."""
    return _detector


def get_parser_registry() -> ParserRegistry:
    """Provide the parser registry (stateless singleton)."""
    return _registry


def get_customer_matcher(customers=Depends(get_customer_repository)) -> CatalogCustomerMatcher:
    """Provide the catalog customer matcher bound to the request session."""
    return CatalogCustomerMatcher(customers)


def get_route_resolver() -> RouteResolver:
    """Provide the route resolver."""
    return RouteResolver()


def get_order_validation_service() -> OrderValidationService:
    """Provide the order validation gate."""
    return OrderValidationService()


def get_process_purchase_order(
    reader=Depends(get_reader),
    detector=Depends(get_detector),
    registry=Depends(get_parser_registry),
    customer_matcher=Depends(get_customer_matcher),
    route_resolver=Depends(get_route_resolver),
    validator=Depends(get_order_validation_service),
    orders=Depends(get_order_repository),
    history=Depends(get_processing_history_repository),
) -> ProcessPurchaseOrder:
    """Provide the ProcessPurchaseOrder use case."""
    return ProcessPurchaseOrder(
        reader,
        detector,
        registry,
        customer_matcher,
        route_resolver,
        validator,
        orders,
        history,
    )


__all__ = [
    "get_create_order",
    "get_customer_matcher",
    "get_customer_repository",
    "get_db",
    "get_detector",
    "get_get_order",
    "get_list_orders",
    "get_order_repository",
    "get_order_validation_service",
    "get_parser_registry",
    "get_process_purchase_order",
    "get_processing_history_repository",
    "get_reader",
    "get_route_repository",
    "get_route_resolver",
    "get_validate_order",
]
