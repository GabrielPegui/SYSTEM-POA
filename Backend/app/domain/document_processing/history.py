"""Processing history domain entity (Pre-Sprint 8.1).

A ``ProcessingHistoryRecord`` is the audit trail of a single PDF processing
attempt. It is intentionally a separate entity from ``Order`` (ADR-003):

- Only a ``PROCESSED`` attempt creates an ``Order``.
- ``REVIEW_REQUIRED`` / ``NO_MATCH`` / ``ERROR`` attempts must never create an
  ``Order``, ``OrderItem``, ``Customer`` or ``Route``; they are only recorded
  here so the business can audit every attempt and why it was not persisted.

The record mirrors ``ProcessedOrderResult`` fields (status, reasons, order
number, parser id, customer/route summary when available, item count) plus an
audit timestamp. It never stores the PDF itself.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.document_processing.processing import ProcessingStatus
from app.domain.validation import require_not_blank, require_valid_optional_id


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class ProcessingHistoryRecord:
    """Audit record of one purchase order processing attempt.

    Fields:

    - ``source_filename`` / ``parser_id``: traceability of the attempt.
    - ``status``: overall outcome (``ProcessingStatus``).
    - ``order_number``: extracted order number, when present (nullable; an
      ``Order`` may or may not have been created).
    - ``processed_at``: audit timestamp of the attempt.
    - ``reasons``: human-readable explanations for the outcome.
    - ``customer_code`` / ``customer_name`` / ``route_code`` /
      ``route_name``: summarized correspondence when available.
    - ``item_count``: number of extracted lines considered.
    """

    source_filename: str
    status: ProcessingStatus
    processed_at: datetime = field(default_factory=_utc_now)
    reasons: tuple[str, ...] = ()
    order_number: str | None = None
    parser_id: str | None = None
    customer_code: str | None = None
    customer_name: str | None = None
    route_code: str | None = None
    route_name: str | None = None
    item_count: int = 0
    id: int | None = None

    def __post_init__(self) -> None:
        require_not_blank("Processing history source filename", self.source_filename)
        require_valid_optional_id("Processing history id", self.id)
        if self.item_count < 0:
            raise ValueError("Processing history item count must not be negative")
