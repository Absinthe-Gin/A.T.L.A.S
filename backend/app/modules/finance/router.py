import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.modules.finance.dependencies import get_finance_service
from app.modules.finance.models import CategoryKind, TransactionKind
from app.modules.finance.schemas import (
    MONTH_PATTERN,
    BudgetCreate,
    BudgetOut,
    BudgetUpdate,
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
    MonthlyReport,
    TransactionCreate,
    TransactionOut,
    TransactionUpdate,
    parse_month,
)
from app.modules.finance.service import FinanceService
from app.modules.users.public import CurrentUser, get_current_user
from app.shared.schemas import Page

User = Annotated[CurrentUser, Depends(get_current_user)]
Service = Annotated[FinanceService, Depends(get_finance_service)]
MonthQuery = Annotated[
    str | None, Query(pattern=MONTH_PATTERN, description="YYYY-MM. Mặc định: tháng hiện tại.")
]


def _month(value: str | None) -> date:
    return parse_month(value) if value else date.today().replace(day=1)


router = APIRouter(tags=["finance"])


# --- Categories --------------------------------------------------------------


@router.get("/finance/categories", response_model=list[CategoryOut])
async def list_categories(
    user: User, service: Service, kind: CategoryKind | None = None
) -> list[CategoryOut]:
    return await service.list_categories(user.id, kind)


@router.post("/finance/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(payload: CategoryCreate, user: User, service: Service) -> CategoryOut:
    return await service.create_category(user.id, payload)


@router.patch("/finance/categories/{category_id}", response_model=CategoryOut)
async def rename_category(
    category_id: uuid.UUID, payload: CategoryUpdate, user: User, service: Service
) -> CategoryOut:
    return await service.rename_category(user.id, category_id, payload)


@router.delete("/finance/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: uuid.UUID, user: User, service: Service) -> Response:
    await service.delete_category(user.id, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Transactions ------------------------------------------------------------


@router.get("/transactions", response_model=Page[TransactionOut])
async def list_transactions(
    user: User,
    service: Service,
    month: MonthQuery = None,
    kind: TransactionKind | None = None,
    category_id: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[TransactionOut]:
    return await service.list_transactions(
        user.id, month=_month(month), kind=kind, category_id=category_id, limit=limit, offset=offset
    )


@router.post("/transactions", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    payload: TransactionCreate, user: User, service: Service
) -> TransactionOut:
    return await service.create_transaction(user.id, payload)


@router.patch("/transactions/{transaction_id}", response_model=TransactionOut)
async def update_transaction(
    transaction_id: uuid.UUID, payload: TransactionUpdate, user: User, service: Service
) -> TransactionOut:
    return await service.update_transaction(user.id, transaction_id, payload)


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(transaction_id: uuid.UUID, user: User, service: Service) -> Response:
    await service.delete_transaction(user.id, transaction_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Budgets -----------------------------------------------------------------


@router.get("/budgets", response_model=list[BudgetOut])
async def list_budgets(user: User, service: Service, month: MonthQuery = None) -> list[BudgetOut]:
    return await service.list_budgets(user.id, _month(month))


@router.post("/budgets", response_model=BudgetOut, status_code=status.HTTP_201_CREATED)
async def create_budget(payload: BudgetCreate, user: User, service: Service) -> BudgetOut:
    return await service.create_budget(user.id, payload)


@router.patch("/budgets/{budget_id}", response_model=BudgetOut)
async def update_budget(
    budget_id: uuid.UUID, payload: BudgetUpdate, user: User, service: Service
) -> BudgetOut:
    return await service.update_budget(user.id, budget_id, payload)


@router.delete("/budgets/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(budget_id: uuid.UUID, user: User, service: Service) -> Response:
    await service.delete_budget(user.id, budget_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Reports -----------------------------------------------------------------


@router.get("/finance/reports/monthly", response_model=MonthlyReport)
async def monthly_report(user: User, service: Service, month: MonthQuery = None) -> MonthlyReport:
    return await service.monthly_report(user.id, _month(month))
