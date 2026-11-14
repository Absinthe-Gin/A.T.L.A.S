"""Shared fixtures.

Tests never read the developer's `.env` and never touch the development
database: every test gets its own settings and its own SQLite file, created
by the real Alembic migrations.
"""

import shutil
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import AppEnvironment, Settings
from app.main import create_app
from tests.database import sqlite_url, upgrade_to_head


def build_test_settings(database_path: Path, **overrides: object) -> Settings:
    values: dict[str, object] = {
        "app_env": AppEnvironment.TESTING,
        "database_url": sqlite_url(database_path),
        "cors_allowed_origins": "http://localhost:5173",
        "log_level": "DEBUG",
    }
    values.update(overrides)
    # `_env_file=None` disables `.env` loading for this instance.
    return Settings(_env_file=None, **values)  # type: ignore[arg-type]


@pytest.fixture(scope="session")
def migrated_database_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A database migrated to head, built once and copied for each test."""
    template = tmp_path_factory.mktemp("database-template") / "template.db"
    upgrade_to_head(template)
    return template


@pytest.fixture
def database_path(tmp_path: Path, migrated_database_template: Path) -> Path:
    """A private, fully migrated database for one test."""
    path = tmp_path / "test.db"
    shutil.copyfile(migrated_database_template, path)
    return path


@pytest.fixture
def settings(database_path: Path) -> Settings:
    return build_test_settings(database_path)


@pytest.fixture
async def app(settings: Settings) -> AsyncIterator[FastAPI]:
    application = create_app(settings)
    async with application.router.lifespan_context(application):
        yield application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    # Unexpected errors must become HTTP 500 responses, as they do in production.
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http_client:
        yield http_client


@pytest.fixture
async def session(app: FastAPI) -> AsyncIterator[AsyncSession]:
    """A database session bound to the test's private database."""
    session_factory: async_sessionmaker[AsyncSession] = app.state.session_factory
    async with session_factory() as db_session:
        yield db_session
