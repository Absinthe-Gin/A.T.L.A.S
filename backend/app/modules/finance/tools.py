"""Finance tools for the assistant. They call FinanceService; they hold no rules of their own.

The model never computes money: totals come from `finance_get_monthly_report`,
and new transactions are proposals the user confirms.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.finance.dependencies import build_finance_service
from app.modules.finance.exceptions import CategoryNotFoundError
from app.modules.finance.models import CategoryKind, TransactionKind
from app.modules.finance.schemas import (
    MAX_AMOUNT,
    MONTH_PATTERN,
    CategoryOut,
    MonthlyReport,
    TransactionCreate,
    TransactionOut,
    parse_month,
)
from app.modules.finance.service import FinanceService, check_amount
from app.shared.tools import Tool, ToolContext, ToolEffect, ToolSpec

DOMAIN = "finance"

_KIND_LABELS = {
    TransactionKind.INCOME: "thu",
    TransactionKind.EXPENSE: "chi",
    TransactionKind.ADJUSTMENT: "điều chỉnh số dư",
}


def format_vnd(amount: int) -> str:
    """`-1250000` → `"-1.250.000 ₫"` (Vietnamese grouping)."""
    return f"{amount:,}".replace(",", ".") + " ₫"


class _FinanceTool:
    """Opens a session for each call: a tool runs outside the HTTP request."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    @asynccontextmanager
    async def _service(self) -> AsyncIterator[FinanceService]:
        async with self._session_factory() as session:
            yield build_finance_service(session)


# --- Monthly report ----------------------------------------------------------


class MonthInput(BaseModel):
    month: str | None = Field(
        default=None, pattern=MONTH_PATTERN, description="Tháng YYYY-MM. Bỏ trống: tháng này."
    )


class GetMonthlyReportTool(_FinanceTool, Tool[MonthInput, MonthlyReport]):
    spec = ToolSpec(
        name="finance_get_monthly_report",
        description=(
            "Tổng thu, tổng chi, điều chỉnh, số dư ròng, chi tiêu theo danh mục và tình trạng "
            "ngân sách của một tháng. Dùng cho mọi câu hỏi về số liệu tài chính."
        ),
        domain=DOMAIN,
        effect=ToolEffect.READ,
        input_model=MonthInput,
        output_model=MonthlyReport,
    )

    async def execute(self, context: ToolContext, tool_input: MonthInput) -> MonthlyReport:
        month = parse_month(tool_input.month) if tool_input.month else date.today().replace(day=1)
        async with self._service() as service:
            return await service.monthly_report(context.user_id, month)


# --- Recent transactions -----------------------------------------------------


class ListTransactionsInput(MonthInput):
    kind: TransactionKind | None = None
    limit: int = Field(default=10, ge=1, le=20)


class TransactionList(BaseModel):
    items: list[TransactionOut]
    total: int


class ListTransactionsTool(_FinanceTool, Tool[ListTransactionsInput, TransactionList]):
    spec = ToolSpec(
        name="finance_list_transactions",
        description="Các giao dịch gần nhất của một tháng, mới nhất trước.",
        domain=DOMAIN,
        effect=ToolEffect.READ,
        input_model=ListTransactionsInput,
        output_model=TransactionList,
    )

    async def execute(
        self, context: ToolContext, tool_input: ListTransactionsInput
    ) -> TransactionList:
        month = parse_month(tool_input.month) if tool_input.month else date.today().replace(day=1)
        async with self._service() as service:
            page = await service.list_transactions(
                context.user_id, month=month, kind=tool_input.kind, limit=tool_input.limit
            )
        return TransactionList(items=page.items, total=page.total)


# --- Categories --------------------------------------------------------------


class ListCategoriesInput(BaseModel):
    kind: CategoryKind | None = None


class CategoryList(BaseModel):
    categories: list[CategoryOut]


class ListCategoriesTool(_FinanceTool, Tool[ListCategoriesInput, CategoryList]):
    spec = ToolSpec(
        name="finance_list_categories",
        description="Danh mục thu và chi của người dùng.",
        domain=DOMAIN,
        effect=ToolEffect.READ,
        input_model=ListCategoriesInput,
        output_model=CategoryList,
    )

    async def execute(self, context: ToolContext, tool_input: ListCategoriesInput) -> CategoryList:
        async with self._service() as service:
            return CategoryList(
                categories=await service.list_categories(context.user_id, tool_input.kind)
            )


# --- New transaction (proposal) ----------------------------------------------


class CreateTransactionInput(BaseModel):
    kind: Literal["income", "expense", "adjustment"] = Field(
        description="income: thu, expense: chi, adjustment: điều chỉnh số dư"
    )
    amount: int = Field(
        ge=-MAX_AMOUNT,
        le=MAX_AMOUNT,
        description="Số đồng, số nguyên. 50k = 50000. Chỉ điều chỉnh mới được âm.",
    )
    category_name: str | None = Field(
        default=None, max_length=60, description="Tên danh mục có sẵn. Bỏ trống nếu không rõ."
    )
    occurred_on: date | None = Field(default=None, description="YYYY-MM-DD. Bỏ trống: hôm nay.")
    note: str | None = Field(default=None, max_length=500)


class CreateTransactionTool(_FinanceTool, Tool[CreateTransactionInput, TransactionOut]):
    spec = ToolSpec(
        name="finance_create_transaction",
        description=(
            "Đề xuất ghi một giao dịch thu, chi hoặc điều chỉnh số dư. "
            "Không lưu ngay: người dùng phải bấm xác nhận."
        ),
        domain=DOMAIN,
        effect=ToolEffect.WRITE,
        input_model=CreateTransactionInput,
        output_model=TransactionOut,
    )

    async def preview(self, context: ToolContext, tool_input: CreateTransactionInput) -> str:
        kind = TransactionKind(tool_input.kind)
        check_amount(kind, tool_input.amount)
        async with self._service() as service:
            category = await self._resolve_category(service, context, tool_input)

        parts = [f"Ghi {_KIND_LABELS[kind]} {format_vnd(tool_input.amount)}"]
        if category is not None:
            parts.append(f"danh mục {category.name}")
        parts.append(f"ngày {(tool_input.occurred_on or date.today()).strftime('%d/%m/%Y')}")
        if tool_input.note:
            parts.append(f"ghi chú: {tool_input.note}")
        return ", ".join(parts) + "."

    async def execute(
        self, context: ToolContext, tool_input: CreateTransactionInput
    ) -> TransactionOut:
        async with self._service() as service:
            category = await self._resolve_category(service, context, tool_input)
            return await service.create_transaction(
                context.user_id,
                TransactionCreate(
                    kind=TransactionKind(tool_input.kind),
                    amount=tool_input.amount,
                    category_id=category.id if category else None,
                    occurred_on=tool_input.occurred_on or date.today(),
                    note=tool_input.note,
                ),
            )

    @staticmethod
    async def _resolve_category(
        service: FinanceService, context: ToolContext, tool_input: CreateTransactionInput
    ) -> CategoryOut | None:
        """The model knows names, not IDs. An unknown name is an error the model can fix."""
        if not tool_input.category_name or tool_input.kind == "adjustment":
            return None
        kind = CategoryKind(tool_input.kind)
        category = await service.find_category_by_name(
            context.user_id, kind, tool_input.category_name
        )
        if category is None:
            available = ", ".join(
                c.name for c in await service.list_categories(context.user_id, kind)
            )
            raise CategoryNotFoundError(
                f"Không có danh mục '{tool_input.category_name}'. Danh mục hiện có: {available}."
            )
        return category


def build_finance_tools(
    session_factory: async_sessionmaker[AsyncSession],
) -> list[Tool[BaseModel, BaseModel]]:
    tools: list[Tool[BaseModel, BaseModel]] = [
        GetMonthlyReportTool(session_factory),  # type: ignore[list-item]
        ListTransactionsTool(session_factory),  # type: ignore[list-item]
        ListCategoriesTool(session_factory),  # type: ignore[list-item]
        CreateTransactionTool(session_factory),  # type: ignore[list-item]
    ]
    return tools
