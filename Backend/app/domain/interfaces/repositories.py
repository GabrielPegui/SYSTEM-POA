"""Repository contracts.

Abstract contracts implemented by the infrastructure layer (SQL Server).
They let the application layer depend on abstractions and stay unaware of
the persistence technology (ADR-001, ADR-003).

The method sets below are the minimal ones needed by the known business
flow (identifying routes, customers and products from documents, and
persisting orders). They will be refined when use cases are implemented.
"""

from abc import ABC, abstractmethod

from app.domain.entities import Customer, Order, Product, Route
from app.domain.enums import OrderStatus


class RouteRepository(ABC):
    """Contract to retrieve routes."""

    @abstractmethod
    def get_by_code(self, code: str) -> Route | None:
        """Return the route matching the given code, or None."""


class CustomerRepository(ABC):
    """Contract to retrieve customers."""

    @abstractmethod
    def get_by_code(self, code: str) -> Customer | None:
        """Return the customer matching the given code, or None."""


class ProductRepository(ABC):
    """Contract to retrieve products from the fixed catalog."""

    @abstractmethod
    def get_by_code(self, code: str) -> Product | None:
        """Return the product matching the given code, or None."""


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
