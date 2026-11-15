"""Database access of the finance module. No business rules here."""

import uuid
from collections.abc import Sequence
from datetime import date

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.finance.models import (
    Budget,
    CategoryKind,
    Transaction,
    TransactionCategory,
    TransactionKind,
)


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(
        self, user_id: uuid.UUID, kind: CategoryKind | None = None
    ) -> Sequence[TransactionCategory]:
        statement = select(TransactionCategory).where(TransactionCategory.user_id == user_id)
        if kind is not None:
            statement = statement.where(TransactionCategory.kind == kind)
        statement = statement.order_by(TransactionCategory.kind, TransactionCategory.name)
        return (await self._session.scalars(statement)).all()

    async def get_for_user(
        self, category_id: uuid.UUID, user_id: uuid.UUID
    ) -> TransactionCategory | None:
        statement = select(TransactionCategory).where(
            TransactionCategory.id == category_id, TransactionCategory.user_id == user_id
        )
        return await self._session.scalar(statement)

    async def add(self, category: TransactionCategory) -> TransactionCategory:
        self._session.add(category)
        await self._session.flush()
        return category

    async def delete(self, category: TransactionCategory) -> None:
        await self._session.delete(category)
        await self._session.flush()

    async def is_in_use(self, category_id: uuid.UUID) -> bool:
        used_by_transactions = exists().where(Transaction.category_id == category_id)
        used_by_budgets = exists().where(Budget.category_id == category_id)
        statement = select(used_by_transactions | used_by_budgets)
        return bool(await self._session.scalar(statement))


class TransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, transaction: Transaction) -> Transaction:
        self._session.add(transaction)
        await self._session.flush()
        return transaction

    async def delete(self, transaction: Transaction) -> None:
        await self._session.delete(transaction)
        await self._session.flush()

    async def get_for_user(
        self, transaction_id: uuid.UUID, user_id: uuid.UUID
    ) -> Transaction | None:
        statement = select(Transaction).where(
            Transaction.id == transaction_id, Transaction.user_id == user_id
        )
        return await self._session.scalar(statement)

    async def list_page(
        self,
        *,
        user_id: uuid.UUID,
        start: date,
        end: date,
        kind: TransactionKind | None,
        category_id: uuid.UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[tuple[Transaction, str | None]], int]:
        """Transactions of a period with their category name, newest first, and the total count."""
        conditions = [
            Transaction.user_id == user_id,
            Transaction.occurred_on >= start,
            Transaction.occurred_on < end,
        ]
        if kind is not None:
            conditions.append(Transaction.kind == kind)
        if category_id is not None:
            conditions.append(Transaction.category_id == category_id)

        rows_statement = (
            select(Transaction, TransactionCategory.name)
            .outerjoin(TransactionCategory, Transaction.category_id == TransactionCategory.id)
            .where(*conditions)
            .order_by(Transaction.occurred_on.desc(), Transaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows: list[tuple[Transaction, str | None]] = [
            (row[0], row[1]) for row in (await self._session.execute(rows_statement)).all()
        ]
        total = await self._session.scalar(
            select(func.count()).select_from(Transaction).where(*conditions)
        )
        return rows, total or 0

    async def category_name(self, category_id: uuid.UUID | None) -> str | None:
        if category_id is None:
            return None
        return await self._session.scalar(
            select(TransactionCategory.name).where(TransactionCategory.id == category_id)
        )

    async def totals_by_kind(
        self, user_id: uuid.UUID, start: date, end: date
    ) -> tuple[dict[TransactionKind, int], int]:
        """Sum of amounts per kind, and the number of transactions, in a period."""
        statement = (
            select(Transaction.kind, func.sum(Transaction.amount), func.count())
            .where(
                Transaction.user_id == user_id,
                Transaction.occurred_on >= start,
                Transaction.occurred_on < end,
            )
            .group_by(Transaction.kind)
        )
        totals: dict[TransactionKind, int] = {}
        count = 0
        for kind, total, rows in (await self._session.execute(statement)).all():
            totals[TransactionKind(kind)] = int(total or 0)
            count += int(rows)
        return totals, count

    async def expense_by_category(
        self, user_id: uuid.UUID, start: date, end: date
    ) -> list[tuple[uuid.UUID | None, str | None, int]]:
        """Spending per category in a period, largest first. Uncategorised spending has no id."""
        total = func.sum(Transaction.amount)
        statement = (
            select(Transaction.category_id, TransactionCategory.name, total)
            .outerjoin(TransactionCategory, Transaction.category_id == TransactionCategory.id)
            .where(
                Transaction.user_id == user_id,
                Transaction.kind == TransactionKind.EXPENSE,
                Transaction.occurred_on >= start,
                Transaction.occurred_on < end,
            )
            .group_by(Transaction.category_id, TransactionCategory.name)
            .order_by(total.desc())
        )
        return [
            (category_id, name, int(amount or 0))
            for category_id, name, amount in (await self._session.execute(statement)).all()
        ]


class BudgetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, budget: Budget) -> Budget:
        self._session.add(budget)
        await self._session.flush()
        return budget

    async def delete(self, budget: Budget) -> None:
        await self._session.delete(budget)
        await self._session.flush()

    async def get_for_user(self, budget_id: uuid.UUID, user_id: uuid.UUID) -> Budget | None:
        statement = select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
        return await self._session.scalar(statement)

    async def find(
        self, user_id: uuid.UUID, month: date, category_id: uuid.UUID | None
    ) -> Budget | None:
        statement = select(Budget).where(
            Budget.user_id == user_id,
            Budget.month == month,
            Budget.category_id.is_(None)
            if category_id is None
            else Budget.category_id == category_id,
        )
        return await self._session.scalar(statement)

    async def list_for_month(
        self, user_id: uuid.UUID, month: date
    ) -> list[tuple[Budget, str | None]]:
        """Budgets of a month with their category name; the overall budget first."""
        statement = (
            select(Budget, TransactionCategory.name)
            .outerjoin(TransactionCategory, Budget.category_id == TransactionCategory.id)
            .where(Budget.user_id == user_id, Budget.month == month)
            .order_by(Budget.category_id.is_not(None), TransactionCategory.name)
        )
        return [(row[0], row[1]) for row in (await self._session.execute(statement)).all()]
