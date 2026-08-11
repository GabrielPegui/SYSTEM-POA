"""SQLAlchemy persistence models.

These models belong to the infrastructure/persistence layer. They are kept
strictly separate from the domain entities (``app.domain.entities``), which
are immutable dataclasses without any ORM dependency (ADR-001, ADR-003).

Schema notes (definitive model):

- Every business table uses a surrogate integer primary key plus a natural
  business key. For ``customers`` the business key is ``(route_id, name)``:
  the customer name is the matching key (``docs/data/CLIENTES POR RUTA.xlsx``)
  and the same name can exist on more than one route (e.g. ``INVERSIONES
  LLERS`` on PPN303 and PPN601), so a composite UNIQUE constraint on
  ``(route_id, name)`` is the persistent uniqueness rule.
- ``customers.route_id`` is a NOT NULL foreign key: every customer row
  belongs to exactly one route (1:1 documented business rule).
- ``orders.status`` stores the string values of ``OrderStatus``.
- ``orders.order_number`` is indexed but NOT unique: order numbering is
  per-customer in the real data; global uniqueness is pending business
  confirmation.
- ``order_items`` stores the product information exactly as printed in the PDF
  (``description``, ``quantity``) plus ``pdf_code``/``ean`` as traceability
  only. There is no product catalog table in the definitive model.
- Monetary values (``unit_price``, ``total``) and presentation (``uom``,
  ``units_per_pack``) belong to the parsing layer (ADR-002), not to the MVP
  schema.
"""

from datetime import UTC, date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Unicode,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def utc_now() -> datetime:
    """Return the current UTC timestamp (used for audit columns)."""
    return datetime.now(UTC)


class RouteModel(Base):
    """Distribution route (``code`` = ``PPN###``)."""

    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    name: Mapped[str | None] = mapped_column(Unicode(255))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    customers: Mapped[list["CustomerModel"]] = relationship(back_populates="route")


class CustomerModel(Base):
    """Customer that sends purchase orders (key: ``(route_id, name)``)."""

    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("route_id", "name", name="uq_customers_route_id_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    address: Mapped[str | None] = mapped_column(Unicode(255))
    route_id: Mapped[int] = mapped_column(
        ForeignKey("routes.id"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    route: Mapped["RouteModel"] = relationship(back_populates="customers")
    orders: Mapped[list["OrderModel"]] = relationship(back_populates="customer")


class OrderModel(Base):
    """Processed purchase order."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="processed", index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    customer: Mapped["CustomerModel"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItemModel"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderItemModel.id",
    )


class OrderItemModel(Base):
    """Line of an order: printed description, quantity and traceability ids."""

    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Unicode(512), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    pdf_code: Mapped[str | None] = mapped_column(String(64))
    ean: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    order: Mapped["OrderModel"] = relationship(back_populates="items")


class ProcessingHistoryModel(Base):
    """Audit record of one purchase order processing attempt (Pre-Sprint 8.1).

    Mirrors ``ProcessingHistoryRecord`` (ADR-003 audit/traceability). Only a
    PROCESSED attempt also creates an ``Order``; the other outcomes exist only
    here. ``reasons`` is stored as JSON (compiles to NVARCHAR(max) on SQL
    Server). No document content is stored.
    """

    __tablename__ = "processing_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_filename: Mapped[str] = mapped_column(Unicode(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    reasons: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    order_number: Mapped[str | None] = mapped_column(String(64), index=True)
    parser_id: Mapped[str | None] = mapped_column(String(64))
    customer_code: Mapped[str | None] = mapped_column(String(32), index=True)
    customer_name: Mapped[str | None] = mapped_column(Unicode(255))
    route_code: Mapped[str | None] = mapped_column(String(20), index=True)
    route_name: Mapped[str | None] = mapped_column(Unicode(255))
    item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
