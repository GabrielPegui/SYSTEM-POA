"""Tests for the persistence schema definition.

These assertions validate the SQLAlchemy model metadata, which is the single
source of truth for the versioned migrations (ADR-003). The actual DDL is
validated separately against SQL Server.
"""

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, Unicode, inspect

from app.database.base import Base


def _table(name):
    return Base.metadata.tables[name]


def test_all_expected_tables_are_registered() -> None:
    tables = set(Base.metadata.tables)
    assert {
        "routes",
        "customers",
        "products",
        "product_route",
        "orders",
        "order_items",
        "processing_history",
    } <= tables


def test_schema_is_created_in_sqlite(engine) -> None:
    table_names = set(inspect(engine).get_table_names())
    assert {
        "routes",
        "customers",
        "products",
        "product_route",
        "orders",
        "order_items",
        "processing_history",
    } <= table_names


def test_routes_schema() -> None:
    table = _table("routes")
    assert [c.name for c in table.columns] == [
        "id",
        "code",
        "name",
        "is_active",
        "created_at",
        "updated_at",
    ]
    assert table.c.id.primary_key
    assert table.c.code.unique
    assert not table.c.code.nullable
    assert table.c.name.nullable
    assert isinstance(table.c.name.type, Unicode)


def test_customers_schema() -> None:
    table = _table("customers")
    assert table.c.code.unique
    assert not table.c.name.nullable
    assert table.c.rnc.nullable
    assert table.c.rnc.index
    assert table.c.route_id.index
    assert any(isinstance(fk, ForeignKey) for fk in table.c.route_id.foreign_keys)


def test_products_schema_and_nullable_ean() -> None:
    table = _table("products")
    assert table.c.code.unique
    assert not table.c.description.nullable
    assert table.c.ean.nullable
    assert table.c.ean.index


def test_product_route_is_n_n_association() -> None:
    table = _table("product_route")
    assert set(table.primary_key.columns.keys()) == {"product_id", "route_id"}
    assert table.c.product_id.foreign_keys
    assert table.c.route_id.foreign_keys


def test_orders_schema() -> None:
    table = _table("orders")
    assert isinstance(table.c.delivery_date.type, Date)
    assert table.c.customer_id.foreign_keys
    assert table.c.customer_id.index
    assert table.c.order_number.index
    assert table.c.status.index
    # order_number is intentionally not globally unique (per-customer numbering).
    assert not table.c.order_number.unique
    assert isinstance(table.c.created_at.type, DateTime)


def test_order_items_schema_and_quantity_rule() -> None:
    table = _table("order_items")
    assert table.c.order_id.foreign_keys
    assert table.c.product_id.foreign_keys
    assert isinstance(table.c.quantity.type, Integer)
    assert any(isinstance(c, CheckConstraint) for c in table.constraints)
    checks = [c for c in table.constraints if isinstance(c, CheckConstraint)]
    assert checks and any("quantity > 0" in str(c.sqltext).lower() for c in checks)


def test_audit_timestamps_present() -> None:
    for name in ("routes", "customers", "products", "orders", "processing_history"):
        assert "created_at" in _table(name).columns
        assert "updated_at" in _table(name).columns


def test_processing_history_schema() -> None:
    table = _table("processing_history")
    assert not table.c.source_filename.nullable
    assert not table.c.source_filename.index
    assert table.c.status.index
    assert table.c.order_number.nullable
    assert table.c.parser_id.nullable
    assert table.c.customer_code.nullable
    assert table.c.route_code.nullable
    assert table.c.reasons.nullable is False
    assert isinstance(table.c.item_count.type, Integer)
    assert isinstance(table.c.processed_at.type, DateTime)

