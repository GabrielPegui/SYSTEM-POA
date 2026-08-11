"""In-memory repository fakes for application use case tests.

These fakes implement the domain repository contracts without any database,
so the application layer can be tested in isolation (no SQL Server needed).
They mirror the persistence behavior relevant to the use cases.
"""

from dataclasses import replace

from app.domain.document_processing.history import ProcessingHistoryRecord
from app.domain.entities import Customer, Order, Route
from app.domain.enums import OrderStatus
from app.domain.interfaces.repositories import (
    CustomerRepository,
    OrderRepository,
    ProcessingHistoryRepository,
    RouteRepository,
)


class InMemoryRouteRepository(RouteRepository):
    """Route repository backed by a code -> Route dict."""

    def __init__(self, routes: list[Route] | None = None) -> None:
        self._by_code = {r.code: r for r in (routes or [])}

    def get_by_code(self, code: str) -> Route | None:
        return self._by_code.get(code)

    def list(self) -> list[Route]:
        return sorted(self._by_code.values(), key=lambda r: r.code)


class InMemoryCustomerRepository(CustomerRepository):
    """Customer repository backed by an in-memory list.

    ``get_by_name`` returns every customer with an exact name match (the
    persistent uniqueness rule is ``(route, name)``, so the same name may
    exist on more than one route).
    """

    def __init__(self, customers: list[Customer] | None = None) -> None:
        self._all = list(customers or [])

    def list(self) -> list[Customer]:
        return sorted(self._all, key=lambda c: c.name)

    def get_by_name(self, name: str) -> tuple[Customer, ...]:
        return tuple(c for c in self._all if c.name == name)


class InMemoryOrderRepository(OrderRepository):
    """Order repository backed by in-memory dicts.

    ``save`` assigns surrogate ids like the persistence implementation and
    mirrors the source-filename identity rule: re-saving the same
    ``source_filename`` replaces the stored order (same surrogate id) instead
    of creating a duplicate. ``update_status`` replaces the stored order with
    the new status. ``delete_all`` empties every stored order.
    """

    def __init__(self) -> None:
        self._by_id: dict[int, Order] = {}
        self._by_number: dict[str, int] = {}
        self._by_filename: dict[str, int] = {}
        self._next_id = 1

    def save(self, order: Order) -> Order:
        existing_id = order.id
        if existing_id is None and order.source_filename is not None:
            existing_id = self._by_filename.get(order.source_filename)
        if existing_id is None:
            existing_id = self._next_id
            self._next_id += 1
        order = replace(order, id=existing_id)
        self._by_id[existing_id] = order
        self._by_number[order.order_number] = existing_id
        if order.source_filename is not None:
            self._by_filename[order.source_filename] = existing_id
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

    def delete_all(self) -> int:
        count = len(self._by_id)
        self._by_id.clear()
        self._by_number.clear()
        self._by_filename.clear()
        return count


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

    def delete_all(self) -> int:
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
