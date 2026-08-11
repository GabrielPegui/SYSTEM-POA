"""ClearDevelopmentOrders use case (development-only cleanup).

Deletes every persisted order together with its items so the frontend "Vaciar
data" action truly empties the working data. It is an intentionally
destructive, development-facing operation:

- It removes DATA only. The tables (``orders``, ``order_items``,
  ``processing_history``) and the Alembic migrations never change; the schema
  and the audit trail are preserved.
- ``processing_history`` is deliberately NOT cleared: it is the audit record
  of every processing attempt (ADR-003). Keeping it after a data reset is a
  truthful trace of what was processed before the cleanup.
- Treating this as a plain order deletion on business endpoints would hide the
  destructive intent, so it is exposed through a dedicated endpoint clearly
  identified as a development cleanup.

The endpoint runs against in-memory fakes during API tests and against
SQL Server in real environments; the FK order ``order_items -> orders`` is
handled by the repository implementation.
"""

from app.domain.interfaces.repositories import OrderRepository


class ClearDevelopmentOrders:
    """Use case that deletes all persisted orders (development cleanup)."""

    def __init__(self, orders: OrderRepository) -> None:
        self._orders = orders

    def execute(self) -> int:
        """Delete every persisted order and its items; return the count."""
        return self._orders.delete_all()