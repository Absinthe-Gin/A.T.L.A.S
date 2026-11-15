from fastapi import Request

from app.infrastructure.external import ExternalServices
from app.modules.food.service import FoodService


def get_food_service(request: Request) -> FoodService:
    external: ExternalServices = request.app.state.external
    return FoodService(external)
