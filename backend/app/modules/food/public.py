"""Public interface of the food module. Other modules import only from here."""

from app.modules.food.tools import build_food_tools

__all__ = ["build_food_tools"]
