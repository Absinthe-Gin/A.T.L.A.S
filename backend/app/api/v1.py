"""Version 1 of the HTTP API: aggregates the routers of every module."""

from fastapi import APIRouter

from app.modules.health.router import router as health_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router)
