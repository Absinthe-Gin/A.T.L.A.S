"""create finance tables and pending actions

Adds the finance tables (categories, transactions, budgets) and the table of
changes proposed by the assistant. Seeds default categories for the local user.

Revision ID: 5d1d9ce9ace0
Revises: d47fdc37c9e9
Create Date: 2026-11-15 07:14:50.465072
"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "5d1d9ce9ace0"
down_revision: str | Sequence[str] | None = "d47fdc37c9e9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The local user created by revision d47fdc37c9e9.
DEFAULT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEFAULT_CATEGORIES = {
    "expense": [
        "Ăn uống",
        "Di chuyển",
        "Mua sắm",
        "Hóa đơn",
        "Giải trí",
        "Sức khỏe",
        "Học tập",
        "Khác",
    ],
    "income": ["Lương", "Thưởng", "Thu nhập khác"],
}


def upgrade() -> None:
    categories = op.create_table(
        "transaction_categories",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column(
            "kind",
            sa.Enum("income", "expense", name="categorykind", native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_transaction_categories_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transaction_categories")),
        sa.UniqueConstraint(
            "user_id", "kind", "name", name=op.f("uq_transaction_categories_user_id_kind_name")
        ),
    )
    op.create_table(
        "ai_pending_actions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("tool_name", sa.String(length=100), nullable=False),
        sa.Column("arguments", sa.JSON(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "confirmed",
                "cancelled",
                "failed",
                name="pendingactionstatus",
                native_enum=False,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name=op.f("fk_ai_pending_actions_conversation_id_conversations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_ai_pending_actions_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_pending_actions")),
    )
    with op.batch_alter_table("ai_pending_actions", schema=None) as batch_op:
        batch_op.create_index(
            "ix_ai_pending_actions_user_id_status", ["user_id", "status"], unique=False
        )

    op.create_table(
        "budgets",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=True),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount > 0", name=op.f("ck_budgets_amount_positive")),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["transaction_categories.id"],
            name=op.f("fk_budgets_category_id_transaction_categories"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_budgets_user_id_users"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_budgets")),
    )
    with op.batch_alter_table("budgets", schema=None) as batch_op:
        batch_op.create_index("ix_budgets_user_id_month", ["user_id", "month"], unique=False)

    op.create_table(
        "transactions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=True),
        sa.Column(
            "kind",
            sa.Enum(
                "income",
                "expense",
                "adjustment",
                name="transactionkind",
                native_enum=False,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount <> 0", name=op.f("ck_transactions_amount_not_zero")),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["transaction_categories.id"],
            name=op.f("fk_transactions_category_id_transaction_categories"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_transactions_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transactions")),
    )
    with op.batch_alter_table("transactions", schema=None) as batch_op:
        batch_op.create_index(
            "ix_transactions_user_id_occurred_on", ["user_id", "occurred_on"], unique=False
        )

    now = datetime.now(UTC)
    op.bulk_insert(
        categories,
        [
            {
                "id": uuid.uuid4(),
                "user_id": DEFAULT_USER_ID,
                "name": name,
                "kind": kind,
                "created_at": now,
                "updated_at": now,
            }
            for kind, names in DEFAULT_CATEGORIES.items()
            for name in names
        ],
    )


def downgrade() -> None:
    # Destructive: removes every transaction, budget, category and pending proposal.
    with op.batch_alter_table("transactions", schema=None) as batch_op:
        batch_op.drop_index("ix_transactions_user_id_occurred_on")

    op.drop_table("transactions")
    with op.batch_alter_table("budgets", schema=None) as batch_op:
        batch_op.drop_index("ix_budgets_user_id_month")

    op.drop_table("budgets")
    with op.batch_alter_table("ai_pending_actions", schema=None) as batch_op:
        batch_op.drop_index("ix_ai_pending_actions_user_id_status")

    op.drop_table("ai_pending_actions")
    op.drop_table("transaction_categories")
