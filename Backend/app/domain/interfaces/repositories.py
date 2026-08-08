"""Repository contracts.

Abstract contracts implemented by the infrastructure layer (SQL Server).
They let the application layer depend on abstractions and stay unaware of
the persistence technology (ADR-001, ADR-003).

The method sets below are the minimal ones needed by the known business
flow (identifying routes, customers and products from documents, and
persisting orders). They will be refined when use cases are implemented.
"""

from abc import ABC, abstractmethod

from app.domain.document_processing.history import ProcessingHistoryRecord
from app.domain.entities import Customer, Order, Product, Route
from app.domain.enums import OrderStatus


class RouteRepository(ABC):
    """Contract to retrieve routes."""

    @abstractmethod
    def get_by_code(self, code: str) -> Route | None:
        """Return the route matching the given code, or None."""


class CustomerRepository(ABC):
    """Contract to retrieve customers.

    ``get_by_rnc`` is needed because the RNC is not a unique identifier
    (``docs/ANALISIS_DATOS_MVP.md``): a single RNC maps to many accounts, so
    the customer matcher must be able to narrow candidates by RNC and then
    disambiguate with the extracted name. ``list`` supports name-based
    matching when the document carries no code/RNC.
    """

    @abstractmethod
    def get_by_code(self, code: str) -> Customer | None:
        """Return the customer matching the given code, or None."""

    @abstractmethod
    def get_by_rnc(self, rnc: str) -> tuple[Customer, ...]:
        """Return every customer matching the given RNC (may be empty)."""

    @abstractmethod
    def list(self) -> list[Customer]:
        """Return the full customer catalog."""


class ProductRepository(ABC):
    """Contract to retrieve products from the fixed catalog.

    ``list`` supports description-based matching against the full catalog
    (the MVP matches by description per ADR-003, since the PDF codes/EANs do
    not correspond to the catalog keys).
    """

    @abstractmethod
    def get_by_code(self, code: str) -> Product | None:
        """Return the product matching the given code, or None."""

    @abstractmethod
    def list(self) -> list[Product]:
        """Return the full product catalog."""


class OrderRepository(ABC):
    """Contract to persist and retrieve orders."""

    @abstractmethod
    def save(self, order: Order) -> Order:
        """Persist an order and return it with its assigned identity."""

    @abstractmethod
    def get_by_number(self, order_number: str) -> Order | None:
        """Return the order matching the given order number, or None."""

    @abstractmethod
    def update_status(self, order_id: int, status: OrderStatus) -> Order:
        """Update the status of an existing order and return it with its new state."""

    @abstractmethod
    def list(self) -> list[Order]:
        """Return the persisted orders, newest first."""


class ProcessingHistoryRepository(ABC):
    """Contract to persist processing attempts (audit trail, ADR-003).

    ``ProcessingHistoryRecord`` is a separate entity from ``Order``: only
    PROCESSED attempts create an order; the other outcomes are only recorded
    here so every attempt is auditable (Pre-Sprint 8.1).
    """

    @abstractmethod
    def save(self, record: ProcessingHistoryRecord) -> ProcessingHistoryRecord:
        """Persist a processing attempt and return it with its assigned identity."""

    @abstractmethod
    def list(self) -> list[ProcessingHistoryRecord]:
        """Return the processing attempts, newest first."""
