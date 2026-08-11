"""OrderItem domain entity."""

from dataclasses import dataclass

from app.domain.validation import (
    require_not_blank,
    require_positive_int,
    require_valid_optional_id,
)


@dataclass(frozen=True)
class OrderItem:
    """A line of an order: the product description and its quantity.

    Lines keep the product information exactly as printed in the PDF
    (``description`` plus ``quantity``). ``pdf_code`` and ``ean`` are
    identifiers found in the document, kept for traceability only; they are
    never used as catalog keys. Monetary values and presentation belong to the
    parsing layer, not to this entity (MVP scope).
    """

    description: str
    quantity: int
    pdf_code: str | None = None
    ean: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        require_not_blank("OrderItem description", self.description)
        require_positive_int("OrderItem quantity", self.quantity)
        require_valid_optional_id("OrderItem id", self.id)
