"""Standard parser output model (ADR-002).

``PurchaseOrderDocument`` is the normalized extraction result every
format-specific parser must return, regardless of the original document
structure.

The parser only extracts the information that actually exists in the PDF. It
never matches against the database, never decides which catalog ``Product``
corresponds and never creates entities. Correspondence is a separate step
handled by ``ProductMatcher`` before any persistence happens.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.domain.document_processing.enums import DocumentType
from app.domain.document_processing.exceptions import DocumentProcessingError


def _require_int(field: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DocumentProcessingError(f"{field} must be an integer")


def _require_positive_int(field: str, value: int) -> None:
    _require_int(field, value)
    if value <= 0:
        raise DocumentProcessingError(f"{field} must be greater than zero")


def _require_decimal(field: str, value: Decimal | None) -> None:
    if value is not None and not isinstance(value, Decimal):
        raise DocumentProcessingError(f"{field} must be a Decimal")


@dataclass(frozen=True)
class PurchaseOrderItemDocument:
    """A single line extracted from a purchase order.

    Only carries information that exists in the PDF:

    - ``description``: the original product description as printed.
    - ``quantity``: requested quantity, always an integer (documented rule).
    - ``pdf_code`` / ``ean``: identifiers found in the document, kept as
      traceability only; they are NOT catalog keys and must never be used to
      select a catalog product (Pre-Sprint 8.1: matching is by description
      per ADR-003). Whether ``pdf_code`` corresponds to the official BOLIN
      catalog code is a pending business question (see the sprint report).
    - ``uom`` / ``units_per_pack``: presentation data from the document.
    - ``unit_price`` / ``total``: monetary values, always ``Decimal``.
    - ``line_number``: position of the line in the document, when available.
    """

    description: str
    quantity: int
    pdf_code: str | None = None
    ean: str | None = None
    uom: str | None = None
    unit_price: Decimal | None = None
    total: Decimal | None = None
    units_per_pack: int | None = None
    line_number: int | None = None

    def __post_init__(self) -> None:
        if not self.description or not self.description.strip():
            raise DocumentProcessingError("Item description must not be blank")
        _require_positive_int("Item quantity", self.quantity)
        _require_decimal("Item unit_price", self.unit_price)
        _require_decimal("Item total", self.total)
        if self.units_per_pack is not None:
            _require_int("Item units_per_pack", self.units_per_pack)
        if self.line_number is not None:
            _require_int("Item line_number", self.line_number)


@dataclass(frozen=True)
class PurchaseOrderDocument:
    """Normalized extraction result of a purchase order PDF.

    Required fields:

    - ``order_number``: the order number as printed in the document.

    Optional/nullable fields (filled only when present in the document):

    - ``customer_code`` / ``customer_name``: extracted customer information.
    - ``route_code``: extracted route when the document carries it.
    - ``order_date`` / ``delivery_date``: dates found in the document.
    - ``source_filename``: original file name (traceability).
    - ``document_type``: detected format that produced this document.
    - ``items``: extracted lines; may be empty when only the header was read.
    """

    order_number: str
    items: tuple[PurchaseOrderItemDocument, ...] = ()
    customer_code: str | None = None
    customer_name: str | None = None
    route_code: str | None = None
    order_date: date | None = None
    delivery_date: date | None = None
    source_filename: str | None = None
    document_type: DocumentType = DocumentType.UNKNOWN

    def __post_init__(self) -> None:
        if not self.order_number or not self.order_number.strip():
            raise DocumentProcessingError("Order number must not be blank")
