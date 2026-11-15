"""Response shapes shared by every module."""

from pydantic import BaseModel


class Page[ItemT](BaseModel):
    """One page of a list that can grow without bound."""

    items: list[ItemT]
    total: int
    limit: int
    offset: int
