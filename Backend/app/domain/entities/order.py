"""Order domain entity."""

from dataclasses import dataclass
from datetime import date, datetime

from app.domain.entities.customer import Customer
from app.domain.entities.order_item import OrderItem
from app.domain.enums import OrderStatus
from app.domain.exceptions import DomainValidationError
from app.domain.validation import require_not_blank, require_valid_optional_id


@dataclass(frozen=True)
class Order:
    """A processed purchase order.

    An order belongs to a customer, has a delivery date and contains one or
    more order items (documented business rules).

    ``status`` defaults to ``OrderStatus.PROCESSED`` because the entity is
    created as a result of document processing (ADR-002); transitioning to
    ``PENDING_VALIDATION``/``VALIDATED`` belongs to the application layer.

    ``source_filename`` is the business identity of a persisted processed
    document: the exact PDF file name. Re-processing the same file name
    updates the existing order (including its items) instead of creating a
    duplicate; a different file name is a different document. Orders created
    through the manual registration flow carry ``None``.
    """

    order_number: str
    customer: Customer
    delivery_date: date
    items: tuple[OrderItem, ...]
    status: OrderStatus = OrderStatus.PROCESSED
    id: int | None = None
    source_filename: str | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        require_not_blank("Order number", self.order_number)
        require_valid_optional_id("Order id", self.id)
        if self.customer is None:
            raise DomainValidationError("Order customer is required")
        if self.delivery_date is None:
            raise DomainValidationError("Order delivery date is required")
        if not self.items:
            raise DomainValidationError("Order must contain at least one item")
