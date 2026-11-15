"""Application factory.

Run with: ``uv run python -m app``
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.v1 import router as api_v1_router
from app.bootstrap import build_ai_runtime
from app.core.config import Settings, get_settings
from app.core.error_handlers import register_error_handlers
from app.core.logging import configure_logging
from app.core.middleware import REQUEST_ID_HEADER, RequestContextMiddleware
from app.infrastructure.database.session import create_engine, create_session_factory
from app.infrastructure.external import build_external_services

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.log_format)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine(settings.database_url)
        app.state.engine = engine
        app.state.session_factory = create_session_factory(engine)
        # One client for every outbound call; each adapter sets its own timeout.
        http_client = httpx.AsyncClient()
        # A test may install its own services or runtime before startup.
        if not hasattr(app.state, "external"):
            app.state.external = build_external_services(settings, http_client)
        if not hasattr(app.state, "ai_runtime"):
            app.state.ai_runtime = build_ai_runtime(
                settings, http_client, app.state.session_factory, app.state.external
            )
        logger.info(
            "Application started",
            extra={
                "environment": settings.app_env.value,
                "version": __version__,
                "llm_provider": app.state.ai_runtime.provider.name,
            },
        )
        try:
            yield
        finally:
            await http_client.aclose()
            await engine.dispose()
            logger.info("Application stopped")

    # Interactive API documentation is a development aid only.
    docs_enabled = not settings.is_production
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs" if docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )
    app.state.settings = settings

    # Middleware added last runs first: CORS wraps everything, so error
    # responses produced further in still carry CORS headers.
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[REQUEST_ID_HEADER],
    )

    register_error_handlers(app)
    app.include_router(api_v1_router)
    return app
