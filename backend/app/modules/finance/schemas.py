"""Request and response shapes of the finance API. Money is whole đồng (int), never float."""

import re
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.finance.models import CategoryKind, TransactionKind

# 1 000 000 000 000 000 đ: far above any personal amount, far below the BigInteger limit.
MAX_AMOUNT = 10**15

MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"
_MONTH = re.compile(MONTH_PATTERN)


def parse_month(value: str) -> date:
    """`"2026-11"` → `date(2026, 11, 1)`."""
    if _MONTH.fullmatch(value) is None:
        raise ValueError("Tháng phải có dạng YYYY-MM.")
    year, month = value.split("-")
    return date(int(year), int(month), 1)


def format_month(value: date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _clean_name(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("Tên danh mục không được để trống.")
    return stripped


# --- Categories --------------------------------------------------------------


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    kind: CategoryKind

    _clean = field_validator("name")(_clean_name)


class CategoryUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=60)

    _clean = field_validator("name")(_clean_name)


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    kind: CategoryKind


# --- Transactions ------------------------------------------------------------


class TransactionCreate(BaseModel):
    kind: TransactionKind
    amount: int = Field(
        ge=-MAX_AMOUNT, le=MAX_AMOUNT, description="Đồng. Chỉ giao dịch điều chỉnh được âm."
    )
    category_id: uuid.UUID | None = None
    occurred_on: date
    note: str | None = Field(default=None, max_length=500)

    _clean_note = field_validator("note")(_clean_text)


class TransactionUpdate(BaseModel):
    """Every field optional; omitted fields keep their value."""

    kind: TransactionKind | None = None
    amount: int | None = Field(default=None, ge=-MAX_AMOUNT, le=MAX_AMOUNT)
    category_id: uuid.UUID | None = None
    occurred_on: date | None = None
    note: str | None = Field(default=None, max_length=500)

    _clean_note = field_validator("note")(_clean_text)


class TransactionOut(BaseModel):
    id: uuid.UUID
    kind: TransactionKind
    amount: int
    currency: str
    category_id: uuid.UUID | None
    category_name: str | None
    occurred_on: date
    note: str | None
    created_at: datetime


# --- Budgets -----------------------------------------------------------------


class BudgetCreate(BaseModel):
    month: str = Field(pattern=MONTH_PATTERN, description="YYYY-MM")
    category_id: uuid.UUID | None = Field(default=None, description="Bỏ trống: ngân sách tổng")
    amount: int = Field(gt=0, le=MAX_AMOUNT)


class BudgetUpdate(BaseModel):
    amount: int = Field(gt=0, le=MAX_AMOUNT)


class BudgetOut(BaseModel):
    id: uuid.UUID
    month: str
    category_id: uuid.UUID | None
    category_name: str | None
    amount: int
    spent: int
    remaining: int
    # Whole percent, rounded down; above 100 means over budget.
    used_percent: int
    over_budget: bool


# --- Reports -----------------------------------------------------------------


class CategoryTotal(BaseModel):
    category_id: uuid.UUID | None
    category_name: str
    total: int


class MonthlyReport(BaseModel):
    month: str
    currency: str
    income_total: int
    expense_total: int
    adjustment_total: int
    # income - expense + adjustment
    net: int
    transaction_count: int
    expense_by_category: list[CategoryTotal]
    budgets: list[BudgetOut]
