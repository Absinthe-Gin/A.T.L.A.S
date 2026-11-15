"""Finance business rules on a real database. Money is whole đồng; totals come from the service."""

import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.finance.dependencies import build_finance_service
from app.modules.finance.exceptions import (
    BudgetExistsError,
    CategoryInUseError,
    CategoryKindMismatchError,
    CategoryNameTakenError,
    CategoryNotFoundError,
    InvalidAmountError,
    TransactionNotFoundError,
)
from app.modules.finance.models import CategoryKind, TransactionKind
from app.modules.finance.schemas import (
    MAX_AMOUNT,
    BudgetCreate,
    BudgetUpdate,
    CategoryCreate,
    CategoryUpdate,
    TransactionCreate,
    TransactionUpdate,
)
from app.modules.finance.service import AdjustmentCategoryError, FinanceService, month_range
from app.modules.users.models import DEFAULT_USER_ID, User

NOV = date(2026, 11, 1)


@pytest.fixture
def finance(session: AsyncSession) -> FinanceService:
    return build_finance_service(session)


async def _category(finance: FinanceService, name: str, kind: CategoryKind) -> uuid.UUID:
    found = await finance.find_category_by_name(DEFAULT_USER_ID, kind, name)
    assert found is not None
    return found.id


async def _add(
    finance: FinanceService,
    kind: TransactionKind,
    amount: int,
    *,
    category: str | None = None,
    on: date = date(2026, 11, 10),
) -> uuid.UUID:
    category_id = None
    if category is not None:
        category_id = await _category(finance, category, CategoryKind(kind.value))
    created = await finance.create_transaction(
        DEFAULT_USER_ID,
        TransactionCreate(kind=kind, amount=amount, category_id=category_id, occurred_on=on),
    )
    return created.id


# --- Month boundaries --------------------------------------------------------


@pytest.mark.parametrize(
    ("month", "expected"),
    [
        (date(2026, 11, 1), (date(2026, 11, 1), date(2026, 12, 1))),
        (date(2026, 12, 15), (date(2026, 12, 1), date(2027, 1, 1))),
        (date(2024, 2, 1), (date(2024, 2, 1), date(2024, 3, 1))),
    ],
)
def test_month_range_covers_the_whole_month(month: date, expected: tuple[date, date]) -> None:
    assert month_range(month) == expected


# --- Categories --------------------------------------------------------------


async def test_default_categories_are_seeded(finance: FinanceService) -> None:
    expense = [c.name for c in await finance.list_categories(DEFAULT_USER_ID, CategoryKind.EXPENSE)]
    income = [c.name for c in await finance.list_categories(DEFAULT_USER_ID, CategoryKind.INCOME)]

    assert "Ăn uống" in expense
    assert "Lương" in income
    assert len(expense) == 8


async def test_category_names_match_regardless_of_case(finance: FinanceService) -> None:
    found = await finance.find_category_by_name(DEFAULT_USER_ID, CategoryKind.EXPENSE, "  ĂN UỐNG ")

    assert found is not None
    assert found.name == "Ăn uống"


async def test_duplicate_category_name_is_rejected_in_any_case(finance: FinanceService) -> None:
    with pytest.raises(CategoryNameTakenError):
        await finance.create_category(
            DEFAULT_USER_ID, CategoryCreate(name="ăn uống", kind=CategoryKind.EXPENSE)
        )


async def test_same_name_is_allowed_for_the_other_kind(finance: FinanceService) -> None:
    created = await finance.create_category(
        DEFAULT_USER_ID, CategoryCreate(name="Ăn uống", kind=CategoryKind.INCOME)
    )

    assert created.kind is CategoryKind.INCOME


async def test_rename_category(finance: FinanceService) -> None:
    category_id = await _category(finance, "Khác", CategoryKind.EXPENSE)

    renamed = await finance.rename_category(
        DEFAULT_USER_ID, category_id, CategoryUpdate(name="Linh tinh")
    )

    assert renamed.name == "Linh tinh"


async def test_category_in_use_cannot_be_deleted(finance: FinanceService) -> None:
    await _add(finance, TransactionKind.EXPENSE, 10_000, category="Giải trí")
    category_id = await _category(finance, "Giải trí", CategoryKind.EXPENSE)

    with pytest.raises(CategoryInUseError):
        await finance.delete_category(DEFAULT_USER_ID, category_id)


async def test_category_used_by_a_budget_cannot_be_deleted(finance: FinanceService) -> None:
    category_id = await _category(finance, "Hóa đơn", CategoryKind.EXPENSE)
    await finance.create_budget(
        DEFAULT_USER_ID, BudgetCreate(month="2026-11", category_id=category_id, amount=1_000_000)
    )

    with pytest.raises(CategoryInUseError):
        await finance.delete_category(DEFAULT_USER_ID, category_id)


async def test_unused_category_can_be_deleted(finance: FinanceService) -> None:
    category_id = await _category(finance, "Học tập", CategoryKind.EXPENSE)

    await finance.delete_category(DEFAULT_USER_ID, category_id)

    assert (
        await finance.find_category_by_name(DEFAULT_USER_ID, CategoryKind.EXPENSE, "Học tập")
        is None
    )


async def test_categories_of_another_user_are_invisible(
    finance: FinanceService, session: AsyncSession
) -> None:
    other = User(display_name="Người khác")
    session.add(other)
    await session.commit()
    category_id = await _category(finance, "Ăn uống", CategoryKind.EXPENSE)

    assert await finance.list_categories(other.id) == []
    with pytest.raises(CategoryNotFoundError):
        await finance.delete_category(other.id, category_id)


# --- Transactions: amounts ---------------------------------------------------


@pytest.mark.parametrize("kind", [TransactionKind.INCOME, TransactionKind.EXPENSE])
@pytest.mark.parametrize("amount", [0, -1, -50_000])
async def test_income_and_expense_must_be_positive(
    finance: FinanceService, kind: TransactionKind, amount: int
) -> None:
    with pytest.raises(InvalidAmountError):
        await _add(finance, kind, amount)


async def test_adjustment_may_be_negative_but_not_zero(finance: FinanceService) -> None:
    await _add(finance, TransactionKind.ADJUSTMENT, -120_000)
    await _add(finance, TransactionKind.ADJUSTMENT, 30_000)

    with pytest.raises(InvalidAmountError):
        await _add(finance, TransactionKind.ADJUSTMENT, 0)


async def test_largest_allowed_amount_is_stored_exactly(finance: FinanceService) -> None:
    await _add(finance, TransactionKind.INCOME, MAX_AMOUNT)

    report = await finance.monthly_report(DEFAULT_USER_ID, NOV)

    assert report.income_total == MAX_AMOUNT
    assert isinstance(report.income_total, int)


async def test_smallest_amount_of_one_dong_is_kept(finance: FinanceService) -> None:
    await _add(finance, TransactionKind.EXPENSE, 1)

    assert (await finance.monthly_report(DEFAULT_USER_ID, NOV)).expense_total == 1


# --- Transactions: categories ------------------------------------------------


async def test_category_must_match_the_transaction_kind(finance: FinanceService) -> None:
    salary = await _category(finance, "Lương", CategoryKind.INCOME)

    with pytest.raises(CategoryKindMismatchError):
        await finance.create_transaction(
            DEFAULT_USER_ID,
            TransactionCreate(
                kind=TransactionKind.EXPENSE, amount=1000, category_id=salary, occurred_on=NOV
            ),
        )


async def test_adjustment_cannot_have_a_category(finance: FinanceService) -> None:
    food = await _category(finance, "Ăn uống", CategoryKind.EXPENSE)

    with pytest.raises(AdjustmentCategoryError):
        await finance.create_transaction(
            DEFAULT_USER_ID,
            TransactionCreate(
                kind=TransactionKind.ADJUSTMENT, amount=1000, category_id=food, occurred_on=NOV
            ),
        )


async def test_unknown_category_is_rejected(finance: FinanceService) -> None:
    with pytest.raises(CategoryNotFoundError):
        await finance.create_transaction(
            DEFAULT_USER_ID,
            TransactionCreate(
                kind=TransactionKind.EXPENSE, amount=1000, category_id=uuid.uuid4(), occurred_on=NOV
            ),
        )


async def test_transaction_without_category_is_allowed(finance: FinanceService) -> None:
    transaction_id = await _add(finance, TransactionKind.EXPENSE, 5_000)

    page = await finance.list_transactions(DEFAULT_USER_ID, month=NOV)

    assert page.items[0].id == transaction_id
    assert page.items[0].category_name is None


# --- Transactions: listing, update, delete -----------------------------------


async def test_listing_is_limited_to_the_month_newest_first(finance: FinanceService) -> None:
    await _add(finance, TransactionKind.EXPENSE, 1, on=date(2026, 10, 31))
    first = await _add(finance, TransactionKind.EXPENSE, 2, on=date(2026, 11, 1))
    last = await _add(finance, TransactionKind.EXPENSE, 3, on=date(2026, 11, 30))
    await _add(finance, TransactionKind.EXPENSE, 4, on=date(2026, 12, 1))

    page = await finance.list_transactions(DEFAULT_USER_ID, month=NOV)

    assert [item.id for item in page.items] == [last, first]
    assert page.total == 2


async def test_listing_paginates_and_filters(finance: FinanceService) -> None:
    for amount in range(1, 6):
        await _add(finance, TransactionKind.EXPENSE, amount * 1000)
    await _add(finance, TransactionKind.INCOME, 9_000_000, category="Lương")

    page = await finance.list_transactions(
        DEFAULT_USER_ID, month=NOV, kind=TransactionKind.EXPENSE, limit=2, offset=2
    )

    assert page.total == 5
    assert len(page.items) == 2
    assert all(item.kind is TransactionKind.EXPENSE for item in page.items)


async def test_update_changes_only_the_given_fields(finance: FinanceService) -> None:
    transaction_id = await _add(finance, TransactionKind.EXPENSE, 10_000, category="Ăn uống")

    updated = await finance.update_transaction(
        DEFAULT_USER_ID, transaction_id, TransactionUpdate(amount=25_000, note="  bữa tối  ")
    )

    assert updated.amount == 25_000
    assert updated.note == "bữa tối"
    assert updated.category_name == "Ăn uống"


async def test_turning_a_transaction_into_an_adjustment_drops_its_category(
    finance: FinanceService,
) -> None:
    transaction_id = await _add(finance, TransactionKind.EXPENSE, 10_000, category="Ăn uống")

    updated = await finance.update_transaction(
        DEFAULT_USER_ID,
        transaction_id,
        TransactionUpdate(kind=TransactionKind.ADJUSTMENT, amount=-10_000),
    )

    assert updated.kind is TransactionKind.ADJUSTMENT
    assert updated.category_id is None


async def test_update_applies_the_same_amount_rules(finance: FinanceService) -> None:
    transaction_id = await _add(finance, TransactionKind.EXPENSE, 10_000)

    with pytest.raises(InvalidAmountError):
        await finance.update_transaction(
            DEFAULT_USER_ID, transaction_id, TransactionUpdate(amount=-5)
        )


async def test_delete_and_missing_transaction(finance: FinanceService) -> None:
    transaction_id = await _add(finance, TransactionKind.EXPENSE, 10_000)

    await finance.delete_transaction(DEFAULT_USER_ID, transaction_id)

    with pytest.raises(TransactionNotFoundError):
        await finance.delete_transaction(DEFAULT_USER_ID, transaction_id)


# --- Budgets and report ------------------------------------------------------


async def test_budget_tracks_spending_of_its_category_and_month(finance: FinanceService) -> None:
    food = await _category(finance, "Ăn uống", CategoryKind.EXPENSE)
    await _add(finance, TransactionKind.EXPENSE, 300_000, category="Ăn uống")
    await _add(finance, TransactionKind.EXPENSE, 250_000, category="Ăn uống")
    await _add(finance, TransactionKind.EXPENSE, 999_000, category="Mua sắm")
    await _add(finance, TransactionKind.EXPENSE, 400_000, category="Ăn uống", on=date(2026, 10, 5))

    budget = await finance.create_budget(
        DEFAULT_USER_ID, BudgetCreate(month="2026-11", category_id=food, amount=500_000)
    )

    assert budget.category_name == "Ăn uống"
    assert budget.spent == 550_000
    assert budget.remaining == -50_000
    assert budget.used_percent == 110
    assert budget.over_budget is True


async def test_overall_budget_counts_all_spending(finance: FinanceService) -> None:
    await _add(finance, TransactionKind.EXPENSE, 100_000, category="Ăn uống")
    await _add(finance, TransactionKind.EXPENSE, 50_000)
    await _add(finance, TransactionKind.INCOME, 10_000_000, category="Lương")

    budget = await finance.create_budget(
        DEFAULT_USER_ID, BudgetCreate(month="2026-11", amount=1_000_000)
    )

    assert budget.category_id is None
    assert budget.spent == 150_000
    assert budget.used_percent == 15
    assert budget.over_budget is False


async def test_budget_exactly_reached_is_not_over(finance: FinanceService) -> None:
    await _add(finance, TransactionKind.EXPENSE, 200_000)

    budget = await finance.create_budget(
        DEFAULT_USER_ID, BudgetCreate(month="2026-11", amount=200_000)
    )

    assert (budget.remaining, budget.used_percent, budget.over_budget) == (0, 100, False)


async def test_one_budget_per_category_and_month(finance: FinanceService) -> None:
    await finance.create_budget(DEFAULT_USER_ID, BudgetCreate(month="2026-11", amount=1_000_000))

    with pytest.raises(BudgetExistsError):
        await finance.create_budget(
            DEFAULT_USER_ID, BudgetCreate(month="2026-11", amount=2_000_000)
        )
    # Another month is a different budget.
    await finance.create_budget(DEFAULT_USER_ID, BudgetCreate(month="2026-12", amount=2_000_000))


async def test_budget_only_for_expense_categories(finance: FinanceService) -> None:
    salary = await _category(finance, "Lương", CategoryKind.INCOME)

    with pytest.raises(CategoryKindMismatchError):
        await finance.create_budget(
            DEFAULT_USER_ID, BudgetCreate(month="2026-11", category_id=salary, amount=1_000)
        )


async def test_update_budget_recomputes_its_status(finance: FinanceService) -> None:
    await _add(finance, TransactionKind.EXPENSE, 600_000)
    budget = await finance.create_budget(
        DEFAULT_USER_ID, BudgetCreate(month="2026-11", amount=500_000)
    )

    updated = await finance.update_budget(DEFAULT_USER_ID, budget.id, BudgetUpdate(amount=800_000))

    assert (updated.remaining, updated.over_budget) == (200_000, False)


async def test_monthly_report_totals(finance: FinanceService) -> None:
    await _add(finance, TransactionKind.INCOME, 15_000_000, category="Lương")
    await _add(finance, TransactionKind.EXPENSE, 120_000, category="Ăn uống")
    await _add(finance, TransactionKind.EXPENSE, 80_000, category="Ăn uống")
    await _add(finance, TransactionKind.EXPENSE, 500_000, category="Hóa đơn")
    await _add(finance, TransactionKind.EXPENSE, 30_000)
    await _add(finance, TransactionKind.ADJUSTMENT, -70_000)
    await _add(finance, TransactionKind.EXPENSE, 1_000_000, on=date(2026, 12, 1))

    report = await finance.monthly_report(DEFAULT_USER_ID, NOV)

    assert report.month == "2026-11"
    assert report.currency == "VND"
    assert report.income_total == 15_000_000
    assert report.expense_total == 730_000
    assert report.adjustment_total == -70_000
    assert report.net == 15_000_000 - 730_000 - 70_000
    assert report.transaction_count == 6
    assert [(c.category_name, c.total) for c in report.expense_by_category] == [
        ("Hóa đơn", 500_000),
        ("Ăn uống", 200_000),
        ("Chưa phân loại", 30_000),
    ]


async def test_empty_month_reports_zeros(finance: FinanceService) -> None:
    report = await finance.monthly_report(DEFAULT_USER_ID, date(2030, 1, 1))

    assert (report.income_total, report.expense_total, report.adjustment_total, report.net) == (
        0,
        0,
        0,
        0,
    )
    assert report.expense_by_category == []
    assert report.budgets == []
