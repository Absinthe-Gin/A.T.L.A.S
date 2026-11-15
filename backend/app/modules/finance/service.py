"""Business rules of personal finance.

Every total is computed here, in whole đồng. The assistant only reads them
(CLAUDE.md, section 4.3).
"""

import logging
import uuid
from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleError
from app.modules.finance.exceptions import (
    BudgetExistsError,
    BudgetNotFoundError,
    CategoryInUseError,
    CategoryKindMismatchError,
    CategoryNameTakenError,
    CategoryNotFoundError,
    InvalidAmountError,
    TransactionNotFoundError,
)
from app.modules.finance.models import (
    DEFAULT_CURRENCY,
    Budget,
    CategoryKind,
    Transaction,
    TransactionCategory,
    TransactionKind,
)
from app.modules.finance.repository import (
    BudgetRepository,
    CategoryRepository,
    TransactionRepository,
)
from app.modules.finance.schemas import (
    BudgetCreate,
    BudgetOut,
    BudgetUpdate,
    CategoryCreate,
    CategoryOut,
    CategoryTotal,
    CategoryUpdate,
    MonthlyReport,
    TransactionCreate,
    TransactionOut,
    TransactionUpdate,
    format_month,
    parse_month,
)
from app.shared.schemas import Page

logger = logging.getLogger(__name__)

UNCATEGORISED = "Chưa phân loại"


def month_range(month: date) -> tuple[date, date]:
    """First day of the month and first day of the next month."""
    start = month.replace(day=1)
    end = date(start.year + 1, 1, 1) if start.month == 12 else date(start.year, start.month + 1, 1)
    return start, end


def check_amount(kind: TransactionKind, amount: int) -> None:
    if kind is TransactionKind.ADJUSTMENT:
        if amount == 0:
            raise InvalidAmountError("Số tiền điều chỉnh phải khác 0.")
    elif amount <= 0:
        raise InvalidAmountError("Số tiền thu hoặc chi phải lớn hơn 0.")


class AdjustmentCategoryError(BusinessRuleError):
    code = "adjustment_has_no_category"
    message = "Giao dịch điều chỉnh số dư không có danh mục."


class FinanceService:
    """Categories, transactions, budgets and reports of one user."""

    def __init__(
        self,
        session: AsyncSession,
        categories: CategoryRepository,
        transactions: TransactionRepository,
        budgets: BudgetRepository,
    ) -> None:
        self._session = session
        self._categories = categories
        self._transactions = transactions
        self._budgets = budgets

    # --- Categories ----------------------------------------------------------

    async def list_categories(
        self, user_id: uuid.UUID, kind: CategoryKind | None = None
    ) -> list[CategoryOut]:
        rows = await self._categories.list_for_user(user_id, kind)
        return [CategoryOut.model_validate(row) for row in rows]

    async def create_category(self, user_id: uuid.UUID, data: CategoryCreate) -> CategoryOut:
        await self._ensure_name_free(user_id, data.kind, data.name)
        category = await self._categories.add(
            TransactionCategory(user_id=user_id, name=data.name, kind=data.kind)
        )
        await self._session.commit()
        return CategoryOut.model_validate(category)

    async def rename_category(
        self, user_id: uuid.UUID, category_id: uuid.UUID, data: CategoryUpdate
    ) -> CategoryOut:
        category = await self._category(user_id, category_id)
        if category.name.casefold() != data.name.casefold():
            await self._ensure_name_free(user_id, category.kind, data.name)
        category.name = data.name
        await self._session.commit()
        return CategoryOut.model_validate(category)

    async def delete_category(self, user_id: uuid.UUID, category_id: uuid.UUID) -> None:
        category = await self._category(user_id, category_id)
        if await self._categories.is_in_use(category.id):
            raise CategoryInUseError()
        await self._categories.delete(category)
        await self._session.commit()

    async def find_category_by_name(
        self, user_id: uuid.UUID, kind: CategoryKind, name: str
    ) -> CategoryOut | None:
        """Case-insensitive match, done in Python: SQLite's lower() ignores Vietnamese letters."""
        wanted = name.strip().casefold()
        for category in await self._categories.list_for_user(user_id, kind):
            if category.name.casefold() == wanted:
                return CategoryOut.model_validate(category)
        return None

    async def _ensure_name_free(self, user_id: uuid.UUID, kind: CategoryKind, name: str) -> None:
        if await self.find_category_by_name(user_id, kind, name) is not None:
            raise CategoryNameTakenError()

    async def _category(self, user_id: uuid.UUID, category_id: uuid.UUID) -> TransactionCategory:
        category = await self._categories.get_for_user(category_id, user_id)
        if category is None:
            raise CategoryNotFoundError()
        return category

    # --- Transactions ----------------------------------------------------------

    async def list_transactions(
        self,
        user_id: uuid.UUID,
        *,
        month: date,
        kind: TransactionKind | None = None,
        category_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Page[TransactionOut]:
        start, end = month_range(month)
        rows, total = await self._transactions.list_page(
            user_id=user_id,
            start=start,
            end=end,
            kind=kind,
            category_id=category_id,
            limit=limit,
            offset=offset,
        )
        return Page[TransactionOut](
            items=[self._out(transaction, name) for transaction, name in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def create_transaction(
        self, user_id: uuid.UUID, data: TransactionCreate
    ) -> TransactionOut:
        await self._check_transaction(user_id, data.kind, data.amount, data.category_id)
        transaction = await self._transactions.add(
            Transaction(
                user_id=user_id,
                kind=data.kind,
                amount=data.amount,
                currency=DEFAULT_CURRENCY,
                category_id=data.category_id,
                occurred_on=data.occurred_on,
                note=data.note,
            )
        )
        await self._session.commit()
        logger.info(
            "Transaction created",
            extra={"transaction_id": str(transaction.id), "kind": transaction.kind.value},
        )
        return self._out(
            transaction, await self._transactions.category_name(transaction.category_id)
        )

    async def update_transaction(
        self, user_id: uuid.UUID, transaction_id: uuid.UUID, data: TransactionUpdate
    ) -> TransactionOut:
        transaction = await self._transaction(user_id, transaction_id)
        changes = data.model_dump(exclude_unset=True)
        kind = changes.get("kind", transaction.kind)
        amount = changes.get("amount", transaction.amount)
        # Turning a transaction into an adjustment drops its category.
        category_id = (
            None
            if kind is TransactionKind.ADJUSTMENT and "category_id" not in changes
            else changes.get("category_id", transaction.category_id)
        )
        await self._check_transaction(user_id, kind, amount, category_id)

        transaction.kind = kind
        transaction.amount = amount
        transaction.category_id = category_id
        if "occurred_on" in changes and changes["occurred_on"] is not None:
            transaction.occurred_on = changes["occurred_on"]
        if "note" in changes:
            transaction.note = changes["note"]
        await self._session.commit()
        return self._out(
            transaction, await self._transactions.category_name(transaction.category_id)
        )

    async def delete_transaction(self, user_id: uuid.UUID, transaction_id: uuid.UUID) -> None:
        transaction = await self._transaction(user_id, transaction_id)
        await self._transactions.delete(transaction)
        await self._session.commit()

    async def _check_transaction(
        self,
        user_id: uuid.UUID,
        kind: TransactionKind,
        amount: int,
        category_id: uuid.UUID | None,
    ) -> None:
        check_amount(kind, amount)
        if category_id is None:
            return
        if kind is TransactionKind.ADJUSTMENT:
            raise AdjustmentCategoryError()
        category = await self._category(user_id, category_id)
        if category.kind.value != kind.value:
            raise CategoryKindMismatchError()

    async def _transaction(self, user_id: uuid.UUID, transaction_id: uuid.UUID) -> Transaction:
        transaction = await self._transactions.get_for_user(transaction_id, user_id)
        if transaction is None:
            raise TransactionNotFoundError()
        return transaction

    @staticmethod
    def _out(transaction: Transaction, category_name: str | None) -> TransactionOut:
        return TransactionOut(
            id=transaction.id,
            kind=transaction.kind,
            amount=transaction.amount,
            currency=transaction.currency,
            category_id=transaction.category_id,
            category_name=category_name,
            occurred_on=transaction.occurred_on,
            note=transaction.note,
            created_at=transaction.created_at,
        )

    # --- Budgets -----------------------------------------------------------------

    async def list_budgets(self, user_id: uuid.UUID, month: date) -> list[BudgetOut]:
        start, end = month_range(month)
        spent_by_category = {
            category_id: total
            for category_id, _, total in await self._transactions.expense_by_category(
                user_id, start, end
            )
        }
        totals, _ = await self._transactions.totals_by_kind(user_id, start, end)
        all_spending = totals.get(TransactionKind.EXPENSE, 0)

        result = []
        for budget, category_name in await self._budgets.list_for_month(user_id, start):
            spent = (
                all_spending
                if budget.category_id is None
                else spent_by_category.get(budget.category_id, 0)
            )
            result.append(self._budget_out(budget, category_name, spent))
        return result

    async def create_budget(self, user_id: uuid.UUID, data: BudgetCreate) -> BudgetOut:
        month = parse_month(data.month)
        category_name: str | None = None
        if data.category_id is not None:
            category = await self._category(user_id, data.category_id)
            if category.kind is not CategoryKind.EXPENSE:
                raise CategoryKindMismatchError("Ngân sách chỉ áp dụng cho danh mục chi.")
            category_name = category.name
        if await self._budgets.find(user_id, month, data.category_id) is not None:
            raise BudgetExistsError()

        try:
            budget = await self._budgets.add(
                Budget(
                    user_id=user_id,
                    month=month,
                    category_id=data.category_id,
                    amount=data.amount,
                    currency=DEFAULT_CURRENCY,
                )
            )
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise BudgetExistsError() from error
        return await self._budget_with_spending(user_id, budget, category_name)

    async def update_budget(
        self, user_id: uuid.UUID, budget_id: uuid.UUID, data: BudgetUpdate
    ) -> BudgetOut:
        budget = await self._budget(user_id, budget_id)
        budget.amount = data.amount
        await self._session.commit()
        category_name = await self._transactions.category_name(budget.category_id)
        return await self._budget_with_spending(user_id, budget, category_name)

    async def delete_budget(self, user_id: uuid.UUID, budget_id: uuid.UUID) -> None:
        budget = await self._budget(user_id, budget_id)
        await self._budgets.delete(budget)
        await self._session.commit()

    async def _budget(self, user_id: uuid.UUID, budget_id: uuid.UUID) -> Budget:
        budget = await self._budgets.get_for_user(budget_id, user_id)
        if budget is None:
            raise BudgetNotFoundError()
        return budget

    async def _budget_with_spending(
        self, user_id: uuid.UUID, budget: Budget, category_name: str | None
    ) -> BudgetOut:
        for item in await self.list_budgets(user_id, budget.month):
            if item.id == budget.id:
                return item
        return self._budget_out(budget, category_name, 0)

    @staticmethod
    def _budget_out(budget: Budget, category_name: str | None, spent: int) -> BudgetOut:
        return BudgetOut(
            id=budget.id,
            month=format_month(budget.month),
            category_id=budget.category_id,
            category_name=category_name,
            amount=budget.amount,
            spent=spent,
            remaining=budget.amount - spent,
            used_percent=spent * 100 // budget.amount,
            over_budget=spent > budget.amount,
        )

    # --- Reports -------------------------------------------------------------------

    async def monthly_report(self, user_id: uuid.UUID, month: date) -> MonthlyReport:
        start, end = month_range(month)
        totals, count = await self._transactions.totals_by_kind(user_id, start, end)
        income = totals.get(TransactionKind.INCOME, 0)
        expense = totals.get(TransactionKind.EXPENSE, 0)
        adjustment = totals.get(TransactionKind.ADJUSTMENT, 0)
        by_category = await self._transactions.expense_by_category(user_id, start, end)

        return MonthlyReport(
            month=format_month(start),
            currency=DEFAULT_CURRENCY,
            income_total=income,
            expense_total=expense,
            adjustment_total=adjustment,
            net=income - expense + adjustment,
            transaction_count=count,
            expense_by_category=[
                CategoryTotal(
                    category_id=category_id, category_name=name or UNCATEGORISED, total=total
                )
                for category_id, name, total in by_category
            ],
            budgets=await self.list_budgets(user_id, start),
        )
