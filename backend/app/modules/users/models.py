import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base, TimestampMixin, UuidPrimaryKeyMixin

# The single local user of the MVP. Created by the first migration; replaced
# by real identities when authentication is introduced (ADR-0007).
DEFAULT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class User(UuidPrimaryKeyMixin, TimestampMixin, Base):
    """Owner of every piece of personal data."""

    __tablename__ = "users"

    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
