"""Travel plans and their itinerary (stored data)."""

import logging
import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.travel.exceptions import (
    DayOutsidePlanError,
    InvalidDateRangeError,
    ItineraryItemNotFoundError,
    TravelPlanNotFoundError,
)
from app.modules.travel.models import ItineraryItem, TravelPlan
from app.modules.travel.repository import TravelRepository
from app.modules.travel.schemas import (
    ItemCreate,
    ItemOut,
    ItemUpdate,
    PlaceRef,
    PlanCreate,
    PlanDetail,
    PlanOut,
    PlanUpdate,
)
from app.shared.schemas import Page

logger = logging.getLogger(__name__)


def _place(name: str | None, lat: float | None, lon: float | None) -> PlaceRef | None:
    """A stored place is always complete: a name together with its coordinates."""
    if name is None or lat is None or lon is None:
        return None
    return PlaceRef(name=name, lat=lat, lon=lon)


def check_dates(start: date | None, end: date | None) -> None:
    if start is not None and end is not None and end < start:
        raise InvalidDateRangeError()


class TravelPlanService:
    def __init__(self, session: AsyncSession, repository: TravelRepository) -> None:
        self._session = session
        self._repository = repository

    async def list_plans(
        self, user_id: uuid.UUID, *, limit: int = 20, offset: int = 0
    ) -> Page[PlanOut]:
        rows = await self._repository.list_plans(user_id, limit=limit, offset=offset)
        return Page(
            items=[self._plan_out(plan, count) for plan, count in rows],
            total=await self._repository.count_plans(user_id),
            limit=limit,
            offset=offset,
        )

    async def get_plan(self, user_id: uuid.UUID, plan_id: uuid.UUID) -> PlanDetail:
        plan = await self._plan(user_id, plan_id, with_items=True)
        return self._detail(plan)

    async def create_plan(self, user_id: uuid.UUID, data: PlanCreate) -> PlanDetail:
        check_dates(data.start_date, data.end_date)
        plan = TravelPlan(
            user_id=user_id,
            title=data.title,
            start_date=data.start_date,
            end_date=data.end_date,
            note=data.note,
        )
        self._set_destination(plan, data.destination)
        await self._repository.add(plan)
        await self._session.commit()
        logger.info("Travel plan created", extra={"plan_id": str(plan.id)})
        return await self.get_plan(user_id, plan.id)

    async def update_plan(
        self, user_id: uuid.UUID, plan_id: uuid.UUID, data: PlanUpdate
    ) -> PlanDetail:
        plan = await self._plan(user_id, plan_id)
        changes = data.model_fields_set
        start = data.start_date if "start_date" in changes else plan.start_date
        end = data.end_date if "end_date" in changes else plan.end_date
        check_dates(start, end)
        if data.title is not None:
            plan.title = data.title.strip()
        if "destination" in changes:
            self._set_destination(plan, data.destination)
        plan.start_date, plan.end_date = start, end
        if "note" in changes:
            plan.note = data.note
        await self._session.commit()
        return await self.get_plan(user_id, plan_id)

    async def delete_plan(self, user_id: uuid.UUID, plan_id: uuid.UUID) -> None:
        plan = await self._plan(user_id, plan_id)
        await self._repository.delete(plan)
        await self._session.commit()

    async def add_item(self, user_id: uuid.UUID, plan_id: uuid.UUID, data: ItemCreate) -> ItemOut:
        plan = await self._plan(user_id, plan_id)
        self._check_day(plan, data.day)
        item = ItineraryItem(
            plan_id=plan.id,
            title=data.title,
            day=data.day,
            start_time=data.start_time,
            note=data.note,
            position=await self._repository.next_position(plan.id),
        )
        self._set_place(item, data.place)
        await self._repository.add(item)
        await self._session.commit()
        return self._item_out(item)

    async def update_item(
        self, user_id: uuid.UUID, plan_id: uuid.UUID, item_id: uuid.UUID, data: ItemUpdate
    ) -> ItemOut:
        plan = await self._plan(user_id, plan_id)
        item = await self._item(plan.id, item_id)
        changes = data.model_fields_set
        if "day" in changes:
            self._check_day(plan, data.day)
            item.day = data.day
        if data.title is not None:
            item.title = data.title.strip()
        if "start_time" in changes:
            item.start_time = data.start_time
        if "place" in changes:
            self._set_place(item, data.place)
        if "note" in changes:
            item.note = data.note
        await self._session.commit()
        return self._item_out(item)

    async def delete_item(self, user_id: uuid.UUID, plan_id: uuid.UUID, item_id: uuid.UUID) -> None:
        plan = await self._plan(user_id, plan_id)
        item = await self._item(plan.id, item_id)
        await self._repository.delete(item)
        await self._session.commit()

    # --- helpers -----------------------------------------------------------------

    async def _plan(
        self, user_id: uuid.UUID, plan_id: uuid.UUID, *, with_items: bool = False
    ) -> TravelPlan:
        plan = await self._repository.get_plan(plan_id, user_id, with_items=with_items)
        if plan is None:
            raise TravelPlanNotFoundError()
        return plan

    async def _item(self, plan_id: uuid.UUID, item_id: uuid.UUID) -> ItineraryItem:
        item = await self._repository.get_item(item_id, plan_id)
        if item is None:
            raise ItineraryItemNotFoundError()
        return item

    @staticmethod
    def _check_day(plan: TravelPlan, day: date | None) -> None:
        if day is None:
            return
        if (plan.start_date and day < plan.start_date) or (plan.end_date and day > plan.end_date):
            raise DayOutsidePlanError()

    @staticmethod
    def _set_destination(plan: TravelPlan, place: PlaceRef | None) -> None:
        plan.destination_name = place.name if place else None
        plan.destination_lat = place.lat if place else None
        plan.destination_lon = place.lon if place else None

    @staticmethod
    def _set_place(item: ItineraryItem, place: PlaceRef | None) -> None:
        item.place_name = place.name if place else None
        item.place_lat = place.lat if place else None
        item.place_lon = place.lon if place else None

    @staticmethod
    def _plan_out(plan: TravelPlan, item_count: int) -> PlanOut:
        return PlanOut(
            id=plan.id,
            title=plan.title,
            destination=_place(plan.destination_name, plan.destination_lat, plan.destination_lon),
            start_date=plan.start_date,
            end_date=plan.end_date,
            note=plan.note,
            item_count=item_count,
            created_at=plan.created_at,
        )

    @staticmethod
    def _item_out(item: ItineraryItem) -> ItemOut:
        return ItemOut(
            id=item.id,
            title=item.title,
            day=item.day,
            start_time=item.start_time,
            place=_place(item.place_name, item.place_lat, item.place_lon),
            note=item.note,
        )

    def _detail(self, plan: TravelPlan) -> PlanDetail:
        base = self._plan_out(plan, len(plan.items))
        return PlanDetail(**base.model_dump(), items=[self._item_out(item) for item in plan.items])
