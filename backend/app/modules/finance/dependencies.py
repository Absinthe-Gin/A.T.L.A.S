from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_session
from app.modules.finance.repository import (
    BudgetRepository,
    CategoryRepository,
    TransactionRepository,
)
from app.modules.finance.service import FinanceService


def build_finance_service(session: AsyncSession) -> FinanceService:
    return FinanceService(
        session=session,
        categories=CategoryRepository(session),
        transactions=TransactionRepository(session),
        budgets=BudgetRepository(session),
    )


def get_finance_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FinanceService:
    return build_finance_service(session)
