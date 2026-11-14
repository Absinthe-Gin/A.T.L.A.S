import uuid
from dataclasses import dataclass

from app.core.exceptions import AppError
from app.modules.users.models import DEFAULT_USER_ID
from app.modules.users.repository import UserRepository


@dataclass(frozen=True)
class CurrentUser:
    """The identity every request acts as."""

    id: uuid.UUID
    display_name: str


class DefaultUserMissingError(AppError):
    code = "default_user_missing"
    message = "Chưa có người dùng mặc định. Hãy chạy migration: `uv run alembic upgrade head`."


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def get_current_user(self) -> CurrentUser:
        """Return the single local user of the MVP (ADR-0007).

        Authentication will replace this lookup without changing callers.
        """
        user = await self._repository.get(DEFAULT_USER_ID)
        if user is None:
            raise DefaultUserMissingError()
        return CurrentUser(id=user.id, display_name=user.display_name)
