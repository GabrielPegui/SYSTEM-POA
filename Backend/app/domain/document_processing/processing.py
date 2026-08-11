"""Workflow result models for the purchase order processing pipeline (Sprint 7).

The full pipeline result is a single, serializable object that the API can
return to the frontend. It always carries enough evidence to explain why an
order was persisted, queued for review or rejected:

- ``PROCESSED``: customer and route resolved; the order was persisted with
  ``OrderStatus.PROCESSED``.
- ``REVIEW_REQUIRED``: some correspondence is not conclusive (ambiguous
  customer, ambiguous route or missing header data). Nothing is persisted.
- ``NO_MATCH``: the customer could not be matched. Nothing is persisted.
- ``ERROR``: the document could not be read, detected or parsed. Nothing is
  persisted.

Safety rule (ADR-003): ``ProcessedOrderResult`` never persists anything on
REVIEW_REQUIRED / NO_MATCH / ERROR; ``order`` is only set on PROCESSED.
"""

import enum
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from app.domain.document_processing.enums import DocumentType
from app.domain.document_processing.matching import CustomerMatchResult
from app.domain.document_processing.purchase_order import PurchaseOrderItemDocument
from app.domain.entities import Order, Route


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ProcessingStatus(enum.Enum):
    """Overall outcome of processing a purchase order document."""

    PROCESSED = "processed"
    REVIEW_REQUIRED = "review_required"
    NO_MATCH = "no_match"
    ERROR = "error"


@dataclass(frozen=True)
class ProcessedOrderResult:
    """Outcome of running the full processing pipeline on a single PDF.

    Fields:

    - ``source_filename`` / ``parser_id`` / ``document_type``: traceability of
      how the document was processed.
    - ``status``: overall outcome (see module docstring).
    - ``order_number`` / ``delivery_date``: extracted header information.
    - ``processed_at``: audit timestamp of the attempt (frontend contract).
    - ``customer_match``: customer correspondence decision.
    - ``route`` / ``route_reason``: resolved route (or why it was not resolved).
    - ``items``: the extracted lines, as printed in the PDF.
    - ``reasons``: human-readable explanations for the overall status.
    - ``order``: the persisted order when ``status`` is PROCESSED.
    """

    source_filename: str
    parser_id: str
    document_type: DocumentType
    status: ProcessingStatus
    processed_at: datetime = field(default_factory=_utc_now)
    order_number: str | None = None
    delivery_date: date | None = None
    customer_code: str | None = None
    customer_name: str | None = None
    customer_match: CustomerMatchResult | None = None
    route: Route | None = None
    route_reason: str = ""
    items: tuple[PurchaseOrderItemDocument, ...] = ()
    reasons: tuple[str, ...] = ()
    order: Order | None = None

    def __post_init__(self) -> None:
        if self.status is ProcessingStatus.PROCESSED and self.order is None:
            raise ValueError("PROCESSED results must carry the persisted order")
        if self.status is not ProcessingStatus.PROCESSED and self.order is not None:
            raise ValueError("Only PROCESSED results may carry a persisted order")
