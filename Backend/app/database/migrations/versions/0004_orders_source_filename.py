"""add orders.source_filename as the persisted document identity

Revision ID: 0004_orders_source_filename
Revises: 0003_definitive_model
Create Date: 2026-08-11

Business rule (persistence fix):

- A persisted order is identified by the exact PDF file name that produced it
  (``source_filename``). Re-processing the same file name updates the existing
  order (including its ``order_items``) instead of inserting a duplicate (a
  repository-level replace). A different file name is a different document.
- ``order_number`` is NOT a deduplication key: it is business data only and
  keeps its existing non-unique index.
- The column is nullable: manual registrations (no source document) and the
  current legacy rows (no filename yet) must remain valid. SQL Server does
  not allow more than one NULL under a regular UNIQUE constraint, so the
  uniqueness is enforced with a FILTERED unique index that only applies to
  non-null values (``WHERE source_filename IS NOT NULL``). This guarantees
  one persisted order per processed file name while unlimited NULLs coexist.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0004_orders_source_filename"
down_revision = "0003_definitive_model"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column("source_filename", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "uq_orders_source_filename",
        "orders",
        ["source_filename"],
        unique=True,
        mssql_where=sa.text("source_filename IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_orders_source_filename", table_name="orders")
    op.drop_column("orders", "source_filename")