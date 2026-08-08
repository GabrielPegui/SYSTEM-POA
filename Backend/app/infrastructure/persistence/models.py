"""SQLAlchemy persistence models.

These models belong to the infrastructure/persistence layer. They are kept
strictly separate from the domain entities (``app.domain.entities``), which
are immutable dataclasses without any ORM dependency (ADR-001, ADR-003).

Schema notes (Sprint 2 - Database Foundation):

- Every business table uses a surrogate integer primary key plus a natural
  business code with a UNIQUE constraint (``code``). This matches the domain
  entities, which expose both ``id`` (assigned by persistence) and ``code``
  (the business key used for matching, e.g. ``CL000168``, ``PPN002``,
  ``01010101``).
- ``customers.route_id`` is a NOT NULL foreign key: the documented business
  rule is one route per customer (2441/2442 records confirmed). The single
  known exception (``CL001062``) is PENDING BUSINESS CONFIRMATION and will be
  handled without schema changes if confirmed (documented in the sprint
  report).
- ``product_route`` is an N:N association table prepared for a future
  catalog-per-route. It is NOT a functional constraint of the MVP: orders
  reference products directly, and products are not forced to belong to a
  route. The cardinality Product<->Route is still under business
  confirmation.
- ``orders.status`` stores the string values of ``OrderStatus``.
- ``orders.order_number`` is indexed but NOT unique: order numbering is
  per-customer in the real data; global uniqueness is pending business
  confirmation.
- ``products.ean`` is nullable (the current catalog has no usable EAN for
  matching; matching is by description in the MVP - ADR-003).
- Monetary values (``unit_price``, ``total``) and presentation (``uom``,
  ``units_per_pack``) belong to the parsing layer (ADR-002), not to the MVP
  schema.
"""

from datetime import UTC, date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Unicode,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def utc_now() -> datetime:
    """Return the current UTC timestamp (used for audit columns)."""
    return datetime.now(UTC)


product_route = Table(
    "product_route",
    Base.metadata,
    Column(
        "product_id",
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "route_id",
        ForeignKey("routes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


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
    products: Mapped[list["ProductModel"]] = relationship(
        secondary=product_route, back_populates="routes"
    )


class CustomerModel(Base):
    """Customer that sends purchase orders (``code`` = ``CL#####[-NNN]``)."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    rnc: Mapped[str | None] = mapped_column(String(20), index=True)
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


class ProductModel(Base):
    """Product from the fixed catalog (``code`` is the 8-digit internal code)."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Unicode(512), nullable=False)
    ean: Mapped[str | None] = mapped_column(String(32), index=True)
    category: Mapped[str | None] = mapped_column(Unicode(128))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    routes: Mapped[list["RouteModel"]] = relationship(
        secondary=product_route, back_populates="products"
    )


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
    """Line of an order: a product and an integer quantity."""

    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    order: Mapped["OrderModel"] = relationship(back_populates="items")
    product: Mapped["ProductModel"] = relationship()


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
