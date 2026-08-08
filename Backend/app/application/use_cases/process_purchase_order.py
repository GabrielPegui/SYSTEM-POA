"""ProcessPurchaseOrder use case (Sprint 7, history added Pre-Sprint 8.1).

Orchestrates the full purchase order workflow:

    PDF -> Reader -> Detector -> ParserRegistry -> Parser
        -> CustomerMatcher -> RouteResolver -> ProductMatcher
        -> OrderValidationService -> OrderRepository.save

Every attempt is recorded in ``ProcessingHistory`` (ADR-003 audit/traceability)
before the result is returned. The history entry reflects the FINAL outcome,
including whether an ``Order`` was actually persisted:

- ``PROCESSED``: customer, route and every item resolved; the order was
  persisted with ``OrderStatus.PROCESSED`` and the history records it.
- ``REVIEW_REQUIRED`` / ``NO_MATCH`` / ``ERROR``: nothing is persisted as an
  order; the attempt is recorded in history only.

Safety rules (ADR-002/ADR-003):

- Nothing is persisted when the document is not recognized, the customer or
  route is not conclusive, or any item is NO_MATCH / REVIEW_REQUIRED.
- Matching never creates catalog entities; ``OrderRepository.save`` raises
  ``CatalogReferenceNotFoundError`` if a reference is missing, and that failure
  is reported as ERROR without partial persistence.
- Processing outcomes (including errors) are returned as a
  ``ProcessedOrderResult``, never raised, so the API can serialize a uniform
  status for the frontend.

Failure handling for history (Pre-Sprint 8.1, Objective B):

- Order persistence failure is recorded in history as ERROR (the order was not
  created, so the audit stays truthful).
- If the history itself cannot be persisted, the exception propagates like any
  unexpected persistence error (consistent with ``OrderRepository``). This is
  a deliberate trade-off: failing loudly is safer than silently losing the
  audit trail. Known residual risk: when the order was already committed and
  only the history write fails, a client retry could create a duplicate order.
  A unit-of-work around order + history is a documented future improvement.
"""

from pathlib import Path

from app.application.services.order_validation import OrderValidationService
from app.application.services.route_resolution import RouteResolver
from app.domain.document_processing.enums import DocumentType
from app.domain.document_processing.exceptions import (
    DocumentProcessingError,
    PDFNoTextError,
    PDFReadError,
)
from app.domain.document_processing.history import ProcessingHistoryRecord
from app.domain.document_processing.processing import (
    ProcessedItemResult,
    ProcessedOrderResult,
    ProcessingStatus,
)
from app.domain.exceptions import CatalogReferenceNotFoundError, DomainError
from app.domain.interfaces import CustomerMatcher, ProductMatcher
from app.domain.interfaces.repositories import (
    OrderRepository,
    ProcessingHistoryRepository,
)
from app.infrastructure.document_processing.detector import DocumentDetector
from app.infrastructure.document_processing.parsers.registry import ParserRegistry
from app.infrastructure.document_processing.reader import PDFReader


class ProcessPurchaseOrder:
    """Use case that processes a PDF purchase order end to end."""

    def __init__(
        self,
        reader: PDFReader,
        detector: DocumentDetector,
        registry: ParserRegistry,
        customer_matcher: CustomerMatcher,
        product_matcher: ProductMatcher,
        route_resolver: RouteResolver,
        validator: OrderValidationService,
        orders: OrderRepository,
        history: ProcessingHistoryRepository,
    ) -> None:
        self._reader = reader
        self._detector = detector
        self._registry = registry
        self._customer_matcher = customer_matcher
        self._product_matcher = product_matcher
        self._route_resolver = route_resolver
        self._validator = validator
        self._orders = orders
        self._history = history

    def execute(self, path: Path, source_filename: str | None = None) -> ProcessedOrderResult:
        path = Path(path)
        filename = source_filename or path.name
        try:
            raw_document = self._reader.read(path, filename=filename)
        except (PDFReadError, PDFNoTextError, DocumentProcessingError) as exc:
            result = self._error_result(filename, reason=str(exc))
            self._record_history(result)
            return result

        detection = self._detector.detect(raw_document)
        if not detection.is_recognized:
            result = self._error_result(
                filename,
                parser_id="unknown",
                document_type=DocumentType.UNKNOWN,
                reason="Document format was not recognized",
            )
            self._record_history(result)
            return result

        try:
            document = self._registry.get(detection.parser_id).parse(raw_document)
        except (DocumentProcessingError, KeyError) as exc:
            result = self._error_result(
                filename,
                parser_id=detection.parser_id,
                document_type=detection.document_type,
                reason=str(exc),
            )
            self._record_history(result)
            return result

        customer_match = self._customer_matcher.match(document.customer_code, document.customer_name)
        route_resolution = self._route_resolver.resolve(customer_match)
        item_results = tuple(
            ProcessedItemResult(item=item, match=self._product_matcher.match(item))
            for item in document.items
        )

        decision = self._validator.evaluate(
            customer_match=customer_match,
            route_resolution=route_resolution,
            item_results=item_results,
            delivery_date=document.delivery_date,
            order_number=document.order_number,
        )

        order = None
        if decision.status is ProcessingStatus.PROCESSED:
            order = self._persist(decision.order)
            if order is None:
                result = self._error_result(
                    filename,
                    parser_id=detection.parser_id,
                    document_type=detection.document_type,
                    reason="Order could not be persisted; catalog reference missing",
                )
                self._record_history(result)
                return result

        result = ProcessedOrderResult(
            source_filename=filename,
            parser_id=detection.parser_id,
            document_type=detection.document_type,
            status=decision.status,
            order_number=document.order_number,
            delivery_date=document.delivery_date,
            customer_match=customer_match,
            route=route_resolution.route,
            route_reason=route_resolution.reason,
            items=item_results,
            reasons=decision.reasons,
            order=order,
        )
        self._record_history(result)
        return result

    def _persist(self, order):
        try:
            return self._orders.save(order)
        except (CatalogReferenceNotFoundError, DomainError):
            return None

    def _record_history(self, result: ProcessedOrderResult) -> None:
        customer = result.customer_match.matched_customer if result.customer_match else None
        route = result.route
        record = ProcessingHistoryRecord(
            source_filename=result.source_filename,
            status=result.status,
            processed_at=result.processed_at,
            reasons=result.reasons,
            order_number=result.order_number,
            parser_id=result.parser_id,
            customer_code=customer.code if customer else None,
            customer_name=customer.name if customer else None,
            route_code=route.code if route else None,
            route_name=route.name if route else None,
            item_count=len(result.items),
        )
        self._history.save(record)

    @staticmethod
    def _error_result(
        source_filename: str,
        reason: str,
        parser_id: str = "unknown",
        document_type: DocumentType = DocumentType.UNKNOWN,
    ) -> ProcessedOrderResult:
        return ProcessedOrderResult(
            source_filename=source_filename,
            parser_id=parser_id,
            document_type=document_type,
            status=ProcessingStatus.ERROR,
            reasons=(reason,),
        )
