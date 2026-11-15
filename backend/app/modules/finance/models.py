import uuid
from datetime import date
from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base, TimestampMixin, UuidPrimaryKeyMixin

DEFAULT_CURRENCY = "VND"


class CategoryKind(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"


class TransactionKind(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"
    # Corrects the balance to match reality; the only kind whose amount may be negative.
    ADJUSTMENT = "adjustment"


def _string_enum(enum_class: type[StrEnum], length: int) -> Enum:
    """Store the enum as a plain string; allowed values are checked by the application."""
    return Enum(
        enum_class,
        native_enum=False,
        create_constraint=False,
        length=length,
        values_callable=lambda members: [member.value for member in members],
        validate_strings=True,
    )


class TransactionCategory(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "transaction_categories"
    __table_args__ = (UniqueConstraint("user_id", "kind", "name"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    kind: Mapped[CategoryKind] = mapped_column(_string_enum(CategoryKind, 20), nullable=False)


class Transaction(UuidPrimaryKeyMixin, TimestampMixin, Base):
    """Money in, money out, or a balance correction. Amounts are whole đồng (ADR-0004)."""

    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_user_id_occurred_on", "user_id", "occurred_on"),
        CheckConstraint("amount <> 0", name="amount_not_zero"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    # A category in use cannot be deleted; adjustments have none.
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("transaction_categories.id", ondelete="RESTRICT")
    )
    kind: Mapped[TransactionKind] = mapped_column(_string_enum(TransactionKind, 20), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default=DEFAULT_CURRENCY)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(String(500))


class Budget(UuidPrimaryKeyMixin, TimestampMixin, Base):
    """A spending limit for one month, for one expense category or for all spending."""

    __tablename__ = "budgets"
    __table_args__ = (
        Index("ix_budgets_user_id_month", "user_id", "month"),
        CheckConstraint("amount > 0", name="amount_positive"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    # Null: the limit applies to all spending of the month.
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("transaction_categories.id", ondelete="RESTRICT")
    )
    # Always the first day of the month.
    month: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default=DEFAULT_CURRENCY)
