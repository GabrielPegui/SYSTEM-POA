"""In-memory repository fakes for application use case tests.

These fakes implement the domain repository contracts without any database,
so the application layer can be tested in isolation (no SQL Server needed).
They mirror the persistence behavior relevant to the use cases.
"""

from dataclasses import replace

from app.domain.document_processing.history import ProcessingHistoryRecord
from app.domain.entities import Customer, Order, Product, Route
from app.domain.enums import OrderStatus
from app.domain.interfaces.repositories import (
    CustomerRepository,
    OrderRepository,
    ProcessingHistoryRepository,
    ProductRepository,
    RouteRepository,
)


class InMemoryRouteRepository(RouteRepository):
    """Route repository backed by a code -> Route dict."""

    def __init__(self, routes: list[Route] | None = None) -> None:
        self._by_code = {r.code: r for r in (routes or [])}

    def get_by_code(self, code: str) -> Route | None:
        return self._by_code.get(code)


class InMemoryCustomerRepository(CustomerRepository):
    """Customer repository backed by a code -> Customer dict.

    ``get_by_rnc`` mirrors the real data: an RNC maps to many accounts
    (``docs/ANALISIS_DATOS_MVP.md``), so it returns a tuple of customers.
    """

    def __init__(self, customers: list[Customer] | None = None) -> None:
        self._by_code = {c.code: c for c in (customers or [])}

    def get_by_code(self, code: str) -> Customer | None:
        return self._by_code.get(code)

    def get_by_rnc(self, rnc: str) -> tuple[Customer, ...]:
        return tuple(c for c in self._by_code.values() if c.rnc == rnc)

    def list(self) -> list[Customer]:
        return sorted(self._by_code.values(), key=lambda c: c.code)


class InMemoryProductRepository(ProductRepository):
    """Product repository backed by a code -> Product dict."""

    def __init__(self, products: list[Product] | None = None) -> None:
        self._by_code = {p.code: p for p in (products or [])}

    def get_by_code(self, code: str) -> Product | None:
        return self._by_code.get(code)

    def list(self) -> list[Product]:
        return sorted(self._by_code.values(), key=lambda p: p.code)


class InMemoryOrderRepository(OrderRepository):
    """Order repository backed by in-memory dicts.

    ``save`` assigns surrogate ids like the persistence implementation;
    ``update_status`` replaces the stored order with the new status.
    """

    def __init__(self) -> None:
        self._by_id: dict[int, Order] = {}
        self._by_number: dict[str, int] = {}
        self._next_id = 1

    def save(self, order: Order) -> Order:
        if order.id is None:
            order = replace(order, id=self._next_id)
            self._next_id += 1
        self._by_id[order.id] = order
        self._by_number[order.order_number] = order.id
        return order

    def get_by_number(self, order_number: str) -> Order | None:
        order_id = self._by_number.get(order_number)
        if order_id is None:
            return None
        return self._by_id.get(order_id)

    def update_status(self, order_id: int, status: OrderStatus) -> Order:
        order = self._by_id.get(order_id)
        if order is None:
            raise RuntimeError(f"Order with id {order_id} was not found")
        updated = replace(order, status=status)
        self._by_id[order_id] = updated
        return updated

    def list(self) -> list[Order]:
        return [self._by_id[order_id] for order_id in sorted(self._by_id, reverse=True)]


class FailingOrderRepository(OrderRepository):
    """Order repository that always fails, simulating a persistence error."""

    def __init__(self, error: Exception) -> None:
        self._error = error

    def save(self, order: Order) -> Order:
        raise self._error

    def get_by_number(self, order_number: str) -> Order | None:
        raise self._error

    def update_status(self, order_id: int, status: OrderStatus) -> Order:
        raise self._error

    def list(self) -> list[Order]:
        raise self._error


class InMemoryProcessingHistoryRepository(ProcessingHistoryRepository):
    """Processing history repository backed by an in-memory list.

    Mirrors the persistence implementation: ``save`` assigns a surrogate id and
    ``list`` returns the attempts newest first.
    """

    def __init__(self) -> None:
        self._records: dict[int, ProcessingHistoryRecord] = {}
        self._next_id = 1

    def save(self, record: ProcessingHistoryRecord) -> ProcessingHistoryRecord:
        if record.id is None:
            record = replace(record, id=self._next_id)
            self._next_id += 1
        self._records[record.id] = record
        return record

    def list(self) -> list[ProcessingHistoryRecord]:
        return [
            self._records[record_id] for record_id in sorted(self._records, reverse=True)
        ]
