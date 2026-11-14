from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_session
from app.modules.users.repository import UserRepository
from app.modules.users.service import CurrentUser, UserService


async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CurrentUser:
    return await UserService(UserRepository(session)).get_current_user()
