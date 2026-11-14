"""The Alembic migrations build, undo and rebuild the schema, and match the models.

These tests are synchronous on purpose: Alembic starts its own event loop.
"""

import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.util.exc import CommandError

from app.modules.users.models import DEFAULT_USER_ID
from tests.database import alembic_config, upgrade_to_head

EXPECTED_TABLES = {"users", "conversations", "messages", "memories"}


def _tables(database_path: Path) -> set[str]:
    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    connection.close()
    return {name for (name,) in rows}


def _query(database_path: Path, sql: str) -> list[tuple[object, ...]]:
    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(sql).fetchall()
    connection.close()
    return rows


@pytest.fixture
def empty_database(tmp_path: Path) -> Path:
    return tmp_path / "migration.db"


def test_upgrade_creates_every_table(empty_database: Path) -> None:
    upgrade_to_head(empty_database)

    assert _tables(empty_database) == EXPECTED_TABLES | {"alembic_version"}


def test_upgrade_creates_the_default_user(empty_database: Path) -> None:
    upgrade_to_head(empty_database)

    rows = _query(empty_database, "SELECT id, display_name FROM users")

    assert rows == [(DEFAULT_USER_ID.hex, "Người dùng")]


def test_upgrade_creates_the_named_constraints_and_indexes(empty_database: Path) -> None:
    upgrade_to_head(empty_database)

    indexes = {
        name
        for (name,) in _query(empty_database, "SELECT name FROM pragma_index_list('conversations')")
    }
    indexes |= {
        name for (name,) in _query(empty_database, "SELECT name FROM pragma_index_list('memories')")
    }
    messages_sql = str(
        _query(empty_database, "SELECT sql FROM sqlite_master WHERE name = 'messages'")[0][0]
    )

    assert "ix_conversations_user_id_updated_at" in indexes
    assert "ix_memories_user_id_category" in indexes
    assert "uq_messages_conversation_id_sequence" in messages_sql
    assert "ck_messages_sequence_non_negative" in messages_sql
    assert "fk_messages_conversation_id_conversations" in messages_sql
    assert "ON DELETE CASCADE" in messages_sql


def test_downgrade_removes_every_table(empty_database: Path) -> None:
    config = alembic_config(empty_database)
    command.upgrade(config, "head")

    command.downgrade(config, "base")

    assert _tables(empty_database) == {"alembic_version"}


def test_schema_can_be_rebuilt_after_a_downgrade(empty_database: Path) -> None:
    config = alembic_config(empty_database)
    command.upgrade(config, "head")
    command.downgrade(config, "base")

    command.upgrade(config, "head")

    assert _tables(empty_database) == EXPECTED_TABLES | {"alembic_version"}
    assert len(_query(empty_database, "SELECT id FROM users")) == 1


def test_models_and_migrations_are_in_sync(empty_database: Path) -> None:
    """Fails when a model changes without a matching migration."""
    config = alembic_config(empty_database)
    command.upgrade(config, "head")

    try:
        command.check(config)
    except CommandError as error:
        pytest.fail(f"Models differ from the migrated schema: {error}")
