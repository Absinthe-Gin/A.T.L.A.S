"""Public interface of the users module. Other modules import only from here."""

from app.modules.users.dependencies import get_current_user
from app.modules.users.service import CurrentUser

__all__ = ["CurrentUser", "get_current_user"]
