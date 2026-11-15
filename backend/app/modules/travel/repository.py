import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.travel.models import ItineraryItem, TravelPlan


class TravelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_plans(
        self, user_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[tuple[TravelPlan, int]]:
        """Plans with their number of items; dated plans first, by start date."""
        counts = (
            select(ItineraryItem.plan_id, func.count().label("item_count"))
            .group_by(ItineraryItem.plan_id)
            .subquery()
        )
        statement = (
            select(TravelPlan, func.coalesce(counts.c.item_count, 0))
            .outerjoin(counts, counts.c.plan_id == TravelPlan.id)
            .where(TravelPlan.user_id == user_id)
            .order_by(
                TravelPlan.start_date.is_(None), TravelPlan.start_date, TravelPlan.created_at.desc()
            )
            .limit(limit)
            .offset(offset)
        )
        return [(row[0], int(row[1])) for row in (await self._session.execute(statement)).all()]

    async def get_plan(
        self, plan_id: uuid.UUID, user_id: uuid.UUID, *, with_items: bool = False
    ) -> TravelPlan | None:
        statement = select(TravelPlan).where(
            TravelPlan.id == plan_id, TravelPlan.user_id == user_id
        )
        if with_items:
            statement = statement.options(selectinload(TravelPlan.items))
        return await self._session.scalar(statement)

    async def count_plans(self, user_id: uuid.UUID) -> int:
        statement = (
            select(func.count()).select_from(TravelPlan).where(TravelPlan.user_id == user_id)
        )
        return int(await self._session.scalar(statement) or 0)

    async def next_position(self, plan_id: uuid.UUID) -> int:
        statement = select(func.max(ItineraryItem.position)).where(ItineraryItem.plan_id == plan_id)
        last = await self._session.scalar(statement)
        return 0 if last is None else last + 1

    async def get_item(self, item_id: uuid.UUID, plan_id: uuid.UUID) -> ItineraryItem | None:
        statement = select(ItineraryItem).where(
            ItineraryItem.id == item_id, ItineraryItem.plan_id == plan_id
        )
        return await self._session.scalar(statement)

    async def add(self, entity: TravelPlan | ItineraryItem) -> None:
        self._session.add(entity)
        await self._session.flush()

    async def delete(self, entity: TravelPlan | ItineraryItem) -> None:
        await self._session.delete(entity)
        await self._session.flush()
