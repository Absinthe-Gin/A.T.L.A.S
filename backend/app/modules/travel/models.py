from __future__ import annotations

import uuid
from datetime import date, time

from sqlalchemy import CheckConstraint, Date, Float, ForeignKey, Index, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, TimestampMixin, UuidPrimaryKeyMixin


class TravelPlan(UuidPrimaryKeyMixin, TimestampMixin, Base):
    """A trip: where to, when, and the itinerary of things to do there."""

    __tablename__ = "travel_plans"
    __table_args__ = (
        Index("ix_travel_plans_user_id_start_date", "user_id", "start_date"),
        CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name="dates_in_order",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    destination_name: Mapped[str | None] = mapped_column(String(200))
    # Coordinates are not money: Float is appropriate here.
    destination_lat: Mapped[float | None] = mapped_column(Float)
    destination_lon: Mapped[float | None] = mapped_column(Float)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    note: Mapped[str | None] = mapped_column(Text)

    items: Mapped[list[ItineraryItem]] = relationship(
        back_populates="plan",
        order_by="(ItineraryItem.day, ItineraryItem.start_time, ItineraryItem.position)",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )


class ItineraryItem(UuidPrimaryKeyMixin, TimestampMixin, Base):
    """One activity in a trip, optionally on a day, at a time and at a place."""

    __tablename__ = "itinerary_items"
    __table_args__ = (Index("ix_itinerary_items_plan_id_day", "plan_id", "day"),)

    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("travel_plans.id", ondelete="CASCADE"), nullable=False
    )
    day: Mapped[date | None] = mapped_column(Date)
    start_time: Mapped[time | None] = mapped_column(Time)
    # Keeps the order of items added without a time.
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    place_name: Mapped[str | None] = mapped_column(String(200))
    place_lat: Mapped[float | None] = mapped_column(Float)
    place_lon: Mapped[float | None] = mapped_column(Float)
    note: Mapped[str | None] = mapped_column(Text)

    plan: Mapped[TravelPlan] = relationship(back_populates="items", lazy="raise")
