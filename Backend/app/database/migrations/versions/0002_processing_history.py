"""processing history table

Revision ID: 0002_processing_history
Revises: 0001_initial_schema
Create Date: 2026-08-08

Pre-Sprint 8.1 - Objective B.

Adds the ``processing_history`` audit table (ADR-003). Only a PROCESSED
attempt creates an ``Order``; REVIEW_REQUIRED / NO_MATCH / ERROR attempts are
recorded only here so every processing attempt is auditable. ``reasons`` is a
JSON column (NVARCHAR(max) on SQL Server). The table stores no document
content.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_processing_history"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "processing_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_filename", sa.Unicode(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("order_number", sa.String(length=64), nullable=True),
        sa.Column("parser_id", sa.String(length=64), nullable=True),
        sa.Column("customer_code", sa.String(length=32), nullable=True),
        sa.Column("customer_name", sa.Unicode(length=255), nullable=True),
        sa.Column("route_code", sa.String(length=20), nullable=True),
        sa.Column("route_name", sa.Unicode(length=255), nullable=True),
        sa.Column("item_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_processing_history"),
    )
    op.create_index("ix_processing_history_status", "processing_history", ["status"])
    op.create_index("ix_processing_history_order_number", "processing_history", ["order_number"])
    op.create_index("ix_processing_history_customer_code", "processing_history", ["customer_code"])
    op.create_index("ix_processing_history_route_code", "processing_history", ["route_code"])


def downgrade() -> None:
    op.drop_index("ix_processing_history_route_code", table_name="processing_history")
    op.drop_index("ix_processing_history_customer_code", table_name="processing_history")
    op.drop_index("ix_processing_history_order_number", table_name="processing_history")
    op.drop_index("ix_processing_history_status", table_name="processing_history")
    op.drop_table("processing_history")
