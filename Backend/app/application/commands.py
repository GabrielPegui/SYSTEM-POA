"""Input commands for the application use cases.

Commands are plain immutable data holders. They are intentionally decoupled
from HTTP (Sprint 4 will map request schemas onto these commands) and from
the domain, so use cases receive already-structured input (ADR-002).
"""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class CreateOrderItemCommand:
    """Input for a single order line: the printed description and quantity."""

    description: str
    quantity: int
    pdf_code: str | None = None
    ean: str | None = None


@dataclass(frozen=True)
class CreateOrderCommand:
    """Input to register a structured purchase order."""

    order_number: str
    customer_name: str
    delivery_date: date
    items: tuple[CreateOrderItemCommand, ...]
