"""Finance tools: what the assistant can read and propose."""

import uuid
from datetime import date

import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.finance.dependencies import build_finance_service
from app.modules.finance.exceptions import CategoryNotFoundError, InvalidAmountError
from app.modules.finance.models import TransactionKind
from app.modules.finance.tools import (
    CreateTransactionInput,
    CreateTransactionTool,
    GetMonthlyReportTool,
    ListCategoriesInput,
    ListCategoriesTool,
    MonthInput,
    build_finance_tools,
    format_vnd,
)
from app.modules.users.models import DEFAULT_USER_ID
from app.shared.tools import ToolContext, ToolEffect

CONTEXT = ToolContext(user_id=DEFAULT_USER_ID, conversation_id=uuid.uuid4())


@pytest.fixture
def factory(app: FastAPI) -> async_sessionmaker[AsyncSession]:
    return app.state.session_factory  # type: ignore[no-any-return]


@pytest.mark.parametrize(
    ("amount", "text"),
    [(0, "0 ₫"), (50000, "50.000 ₫"), (1_250_000, "1.250.000 ₫"), (-70000, "-70.000 ₫")],
)
def test_format_vnd(amount: int, text: str) -> None:
    assert format_vnd(amount) == text


def test_only_the_create_tool_writes(factory: async_sessionmaker[AsyncSession]) -> None:
    tools = {tool.spec.name: tool.spec.effect for tool in build_finance_tools(factory)}

    assert tools == {
        "finance_get_monthly_report": ToolEffect.READ,
        "finance_list_transactions": ToolEffect.READ,
        "finance_list_categories": ToolEffect.READ,
        "finance_create_transaction": ToolEffect.WRITE,
    }


async def test_preview_describes_the_change_without_saving(
    factory: async_sessionmaker[AsyncSession], session: AsyncSession
) -> None:
    tool = CreateTransactionTool(factory)

    summary = await tool.preview(
        CONTEXT,
        CreateTransactionInput(
            kind="expense",
            amount=50000,
            category_name="ăn uống",
            occurred_on=date(2026, 11, 15),
            note="phở",
        ),
    )

    assert summary == "Ghi chi 50.000 ₫, danh mục Ăn uống, ngày 15/11/2026, ghi chú: phở."
    report = await build_finance_service(session).monthly_report(DEFAULT_USER_ID, date(2026, 11, 1))
    assert report.transaction_count == 0


async def test_preview_rejects_an_unknown_category_and_lists_the_real_ones(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    tool = CreateTransactionTool(factory)

    with pytest.raises(CategoryNotFoundError) as error:
        await tool.preview(
            CONTEXT, CreateTransactionInput(kind="expense", amount=1000, category_name="Cà phê")
        )

    assert "Ăn uống" in error.value.message


async def test_preview_applies_the_amount_rules(factory: async_sessionmaker[AsyncSession]) -> None:
    with pytest.raises(InvalidAmountError):
        await CreateTransactionTool(factory).preview(
            CONTEXT, CreateTransactionInput(kind="expense", amount=-5)
        )


async def test_execute_creates_the_transaction(factory: async_sessionmaker[AsyncSession]) -> None:
    tool = CreateTransactionTool(factory)

    created = await tool.execute(
        CONTEXT, CreateTransactionInput(kind="income", amount=2_000_000, category_name="Thưởng")
    )

    assert created.kind is TransactionKind.INCOME
    assert created.category_name == "Thưởng"
    assert created.occurred_on == date.today()


async def test_adjustment_ignores_a_category_name(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    created = await CreateTransactionTool(factory).execute(
        CONTEXT, CreateTransactionInput(kind="adjustment", amount=-30000, category_name="Ăn uống")
    )

    assert created.category_id is None


async def test_report_tool_returns_backend_totals(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    await CreateTransactionTool(factory).execute(
        CONTEXT, CreateTransactionInput(kind="expense", amount=40000, occurred_on=date(2026, 11, 3))
    )

    report = await GetMonthlyReportTool(factory).execute(CONTEXT, MonthInput(month="2026-11"))

    assert report.expense_total == 40000


async def test_categories_tool(factory: async_sessionmaker[AsyncSession]) -> None:
    result = await ListCategoriesTool(factory).execute(CONTEXT, ListCategoriesInput(kind=None))

    assert len(result.categories) == 11
