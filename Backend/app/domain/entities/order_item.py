"""OrderItem domain entity."""

from dataclasses import dataclass

from app.domain.entities.product import Product
from app.domain.exceptions import DomainValidationError
from app.domain.validation import require_positive_int, require_valid_optional_id


@dataclass(frozen=True)
class OrderItem:
    """A line of an order: a product and its quantity.

    ``quantity`` is an integer number of units/cases, matching the Cantidad
    column in the real source documents (integer per document analysis).
    Monetary values (unit price, line total) and presentation (uom, units per
    pack) belong to the parsing layer, not to this entity (MVP scope).
    """

    product: Product
    quantity: int
    id: int | None = None

    def __post_init__(self) -> None:
        if self.product is None:
            raise DomainValidationError("OrderItem product is required")
        require_positive_int("OrderItem quantity", self.quantity)
        require_valid_optional_id("OrderItem id", self.id)
