"""create travel tables

Travel plans and their itinerary items. New tables only: no existing data changes.

Revision ID: b69b5ed32a34
Revises: 5d1d9ce9ace0
Create Date: 2026-11-15 16:59:11.381306
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b69b5ed32a34"
down_revision: str | Sequence[str] | None = "5d1d9ce9ace0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "travel_plans",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("destination_name", sa.String(length=200), nullable=True),
        sa.Column("destination_lat", sa.Float(), nullable=True),
        sa.Column("destination_lon", sa.Float(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name=op.f("ck_travel_plans_dates_in_order"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_travel_plans_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_travel_plans")),
    )
    with op.batch_alter_table("travel_plans", schema=None) as batch_op:
        batch_op.create_index(
            "ix_travel_plans_user_id_start_date", ["user_id", "start_date"], unique=False
        )

    op.create_table(
        "itinerary_items",
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("day", sa.Date(), nullable=True),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("place_name", sa.String(length=200), nullable=True),
        sa.Column("place_lat", sa.Float(), nullable=True),
        sa.Column("place_lon", sa.Float(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["travel_plans.id"],
            name=op.f("fk_itinerary_items_plan_id_travel_plans"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_itinerary_items")),
    )
    with op.batch_alter_table("itinerary_items", schema=None) as batch_op:
        batch_op.create_index("ix_itinerary_items_plan_id_day", ["plan_id", "day"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("itinerary_items", schema=None) as batch_op:
        batch_op.drop_index("ix_itinerary_items_plan_id_day")

    op.drop_table("itinerary_items")
    with op.batch_alter_table("travel_plans", schema=None) as batch_op:
        batch_op.drop_index("ix_travel_plans_user_id_start_date")

    op.drop_table("travel_plans")
