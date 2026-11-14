import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.core.config import Settings
from app.infrastructure.database.session import ping_database
from app.modules.health.schemas import CheckStatus, HealthChecks, HealthResponse, HealthStatus

logger = logging.getLogger(__name__)


class HealthService:
    """Report whether the application and its required dependencies work."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    async def check(self) -> HealthResponse:
        database = await self._check_database()
        status = HealthStatus.OK if database is CheckStatus.OK else HealthStatus.DEGRADED
        return HealthResponse(
            status=status,
            environment=self._settings.app_env.value,
            version=__version__,
            checks=HealthChecks(database=database),
        )

    async def _check_database(self) -> CheckStatus:
        try:
            await ping_database(self._session)
        except SQLAlchemyError:
            logger.exception("Database health check failed")
            return CheckStatus.ERROR
        return CheckStatus.OK
