"""phase 7 resilience

Revision ID: 0002_phase7_resilience
Revises: 0001_initial
Create Date: 2026-09-09 00:00:00
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_phase7_resilience"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def _columns(inspector, table):
    return {column["name"] for column in inspector.get_columns(table)}


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = set(inspector.get_table_names())
    if "sales" in tables:
        columns = _columns(inspector, "sales")
        additions = {
            "offline_operation_id": sa.Column("offline_operation_id", sa.String(80), nullable=True),
            "device_id": sa.Column("device_id", sa.String(80), nullable=True),
            "local_created_at": sa.Column("local_created_at", sa.DateTime(), nullable=True),
            "sync_status": sa.Column("sync_status", sa.String(30), nullable=False, server_default="SYNCED"),
            "sync_conflict": sa.Column("sync_conflict", sa.Text(), nullable=True),
        }
        for name, column in additions.items():
            if name not in columns:
                op.add_column("sales", column)
        indexes = {index["name"] for index in sa.inspect(connection).get_indexes("sales")}
        if "uq_sales_account_idempotency" not in indexes and {"account_id", "idempotency_key"}.issubset(columns):
            op.create_index("uq_sales_account_idempotency", "sales", ["account_id", "idempotency_key"], unique=True)
        if "uq_sales_account_offline_operation" not in indexes and "account_id" in columns:
            op.create_index("uq_sales_account_offline_operation", "sales", ["account_id", "offline_operation_id"], unique=True)

    if "sync_operation_logs" not in tables and {"accounts", "users"}.issubset(tables):
        op.create_table(
            "sync_operation_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("operation_id", sa.String(80), nullable=False),
            sa.Column("operation_type", sa.String(40), nullable=False),
            sa.Column("device_id", sa.String(80), nullable=False),
            sa.Column("status", sa.String(30), nullable=False),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("conflict", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("error_category", sa.String(40), nullable=True),
            sa.Column("error_message", sa.String(255), nullable=True),
            sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("account_id", "operation_id", name="uq_sync_log_account_operation"),
        )
        op.create_index("ix_sync_logs_account_status", "sync_operation_logs", ["account_id", "status", "updated_at"])
        op.create_index("ix_sync_logs_device", "sync_operation_logs", ["account_id", "device_id"])


def downgrade() -> None:
    connection = op.get_bind()
    tables = set(sa.inspect(connection).get_table_names())
    if "sync_operation_logs" in tables:
        op.drop_table("sync_operation_logs")
    if "sales" in tables:
        indexes = {index["name"] for index in sa.inspect(connection).get_indexes("sales")}
        for name in ("uq_sales_account_offline_operation", "uq_sales_account_idempotency"):
            if name in indexes:
                op.drop_index(name, table_name="sales")
        columns = _columns(sa.inspect(connection), "sales")
        for name in ("sync_conflict", "sync_status", "local_created_at", "device_id", "offline_operation_id"):
            if name in columns:
                op.drop_column("sales", name)
