"""definitive business model (name-based customers, no product catalog)

Revision ID: 0003_definitive_model
Revises: 0002_processing_history
Create Date: 2026-08-10

Adopts the definitive business model (Pre-Sprint 9):

- Customers are identified by ``(route_id, name)``: the ``code`` and ``rnc``
  columns are removed and ``address`` is added. A composite UNIQUE constraint
  on ``(route_id, name)`` replaces ``uq_customers_code`` because the same
  customer name can exist on more than one route (e.g. ``INVERSIONES LLERS``
  on PPN303 and PPN601).
- The product catalog is removed: ``products`` and the ``product_route``
  association are dropped, and ``order_items`` no longer references
  ``products.id``. Order lines now store the product ``description`` exactly
  as printed in the PDF plus ``pdf_code``/``ean`` as traceability only.

Data migration: legacy order items reference the removed product catalog and
hold no description under the new model. The ``description`` column is added
nullable, backfilled with a ``(legacy)`` marker, then constrained NOT NULL so
existing order rows (order number, customer, dates, status) are preserved for
audit. New orders always carry the real printed description.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_definitive_model"
down_revision = "0002_processing_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- order_items: drop product reference, add printed description. ---
    op.drop_index("ix_order_items_product_id", table_name="order_items")
    op.drop_constraint(
        "fk_order_items_product_id_products", "order_items", type_="foreignkey"
    )
    op.drop_column("order_items", "product_id")

    op.add_column(
        "order_items",
        sa.Column("description", sa.Unicode(length=512), nullable=True),
    )
    op.execute("UPDATE order_items SET description = '(legacy)' WHERE description IS NULL")
    op.alter_column("order_items", "description", existing_type=sa.Unicode(length=512), nullable=False)
    op.add_column("order_items", sa.Column("pdf_code", sa.String(length=64), nullable=True))
    op.add_column("order_items", sa.Column("ean", sa.String(length=32), nullable=True))

    # --- customers: name is the business key (with route). ---
    op.drop_constraint("uq_customers_code", "customers", type_="unique")
    op.drop_column("customers", "code")
    op.drop_index("ix_customers_rnc", table_name="customers")
    op.drop_column("customers", "rnc")
    op.add_column("customers", sa.Column("address", sa.Unicode(length=255), nullable=True))
    op.create_unique_constraint(
        "uq_customers_route_id_name", "customers", ["route_id", "name"]
    )

    # --- products: catalog removed. ---
    op.drop_table("product_route")
    op.drop_table("products")


def downgrade() -> None:
    # NOTE: legacy product data cannot be restored; structure is recreated.
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Unicode(length=512), nullable=False),
        sa.Column("ean", sa.String(length=32), nullable=True),
        sa.Column("category", sa.Unicode(length=128), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_products"),
        sa.UniqueConstraint("code", name="uq_products_code"),
    )
    op.create_index("ix_products_ean", "products", ["ean"])

    op.create_table(
        "product_route",
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("route_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"],
            name="fk_product_route_product_id_products", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["route_id"], ["routes.id"],
            name="fk_product_route_route_id_routes", ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("product_id", "route_id", name="pk_product_route"),
    )

    op.drop_constraint("uq_customers_route_id_name", "customers", type_="unique")
    op.drop_column("customers", "address")
    op.add_column("customers", sa.Column("rnc", sa.String(length=20), nullable=True))
    op.create_index("ix_customers_rnc", "customers", ["rnc"])
    op.add_column("customers", sa.Column("code", sa.String(length=32), nullable=True))
    op.execute("UPDATE customers SET code = CAST(id AS VARCHAR(32)) WHERE code IS NULL")
    op.alter_column("customers", "code", existing_type=sa.String(length=32), nullable=False)
    op.create_unique_constraint("uq_customers_code", "customers", ["code"])

    op.drop_column("order_items", "ean")
    op.drop_column("order_items", "pdf_code")
    op.add_column(
        "order_items",
        sa.Column("product_id", sa.Integer(), nullable=True),
    )
    op.execute("DELETE FROM order_items WHERE description = '(legacy)'")
    op.alter_column("order_items", "description", nullable=True)
    op.create_foreign_key(
        "fk_order_items_product_id_products",
        "order_items",
        "products",
        ["product_id"],
        ["id"],
    )
    op.create_index("ix_order_items_product_id", "order_items", ["product_id"])
