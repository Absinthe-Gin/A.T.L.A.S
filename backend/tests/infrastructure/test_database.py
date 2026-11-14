from pathlib import Path

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.database.session import (
    create_engine,
    create_session_factory,
    ping_database,
)


def _url(path: Path) -> str:
    return f"sqlite+aiosqlite:///{path.as_posix()}"


async def test_engine_creates_the_database_directory(tmp_path: Path) -> None:
    database_path = tmp_path / "nested" / "data" / "app.db"

    engine = create_engine(_url(database_path))
    try:
        async with create_session_factory(engine)() as session:
            await ping_database(session)
    finally:
        await engine.dispose()

    assert database_path.exists()


async def test_creating_the_engine_does_not_open_a_connection(tmp_path: Path) -> None:
    database_path = tmp_path / "lazy.db"

    engine = create_engine(_url(database_path))
    await engine.dispose()

    assert not database_path.exists()


async def test_sqlite_connections_enforce_foreign_keys(app: FastAPI) -> None:
    session_factory: async_sessionmaker[AsyncSession] = app.state.session_factory

    async with session_factory() as session:
        foreign_keys = (await session.execute(text("PRAGMA foreign_keys"))).scalar_one()
        journal_mode = (await session.execute(text("PRAGMA journal_mode"))).scalar_one()

    assert foreign_keys == 1
    assert journal_mode == "wal"


async def test_in_memory_database_is_supported() -> None:
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with create_session_factory(engine)() as session:
            await ping_database(session)
    finally:
        await engine.dispose()
