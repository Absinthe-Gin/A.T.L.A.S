"""Database engine and session management."""

from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import Request
from sqlalchemy import URL, event, make_url, select
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import ConnectionPoolEntry

_SQLITE_IN_MEMORY = ":memory:"


def _is_sqlite(url: URL) -> bool:
    return url.get_backend_name() == "sqlite"


def _ensure_sqlite_directory(url: URL) -> None:
    """Create the parent directory of a file-based SQLite database."""
    if url.database and url.database != _SQLITE_IN_MEMORY:
        Path(url.database).parent.mkdir(parents=True, exist_ok=True)


def _configure_sqlite_connection(
    dbapi_connection: DBAPIConnection, _connection_record: ConnectionPoolEntry
) -> None:
    cursor = dbapi_connection.cursor()
    try:
        # SQLite does not enforce foreign keys unless asked on each connection.
        cursor.execute("PRAGMA foreign_keys=ON")
        # WAL lets readers proceed while a write is in progress.
        cursor.execute("PRAGMA journal_mode=WAL")
    finally:
        cursor.close()


def create_engine(database_url: str) -> AsyncEngine:
    """Create the async engine. No connection is opened until first use."""
    url = make_url(database_url)
    if _is_sqlite(url):
        _ensure_sqlite_directory(url)

    engine = create_async_engine(url)

    if _is_sqlite(url):
        event.listen(engine.sync_engine, "connect", _configure_sqlite_connection)
    return engine


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    # Objects stay usable after commit; implicit refresh I/O is not possible in async code.
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one session per request.

    Services own the transaction boundary and call ``commit()``. Anything
    left uncommitted is rolled back when the session closes.
    """
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def ping_database(session: AsyncSession) -> None:
    """Run a trivial query. Raises ``SQLAlchemyError`` if the database is unreachable."""
    await session.execute(select(1))
