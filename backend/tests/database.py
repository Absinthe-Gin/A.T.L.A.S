"""Helpers for running Alembic migrations against a test database."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.finance.models import TransactionCategory
from app.modules.users.models import User

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def sqlite_url(database_path: Path) -> str:
    return f"sqlite+aiosqlite:///{database_path.as_posix()}"


def alembic_config(database_path: Path) -> Config:
    """Alembic configuration aimed at `database_path`.

    Built without `alembic.ini` so running migrations does not reconfigure
    logging in the middle of a test run.
    """
    config = Config()
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    # Alembic passes option values through `%` interpolation.
    config.set_main_option("sqlalchemy.url", sqlite_url(database_path).replace("%", "%%"))
    return config


def upgrade_to_head(database_path: Path) -> None:
    command.upgrade(alembic_config(database_path), "head")


async def remove_default_user(session: AsyncSession) -> None:
    """Simulate a database whose default user is missing (it owns the seeded categories)."""
    await session.execute(delete(TransactionCategory))
    await session.execute(delete(User))
    await session.commit()
