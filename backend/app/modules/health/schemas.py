from enum import StrEnum

from pydantic import BaseModel


class HealthStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"


class CheckStatus(StrEnum):
    OK = "ok"
    ERROR = "error"


class HealthChecks(BaseModel):
    database: CheckStatus


class HealthResponse(BaseModel):
    status: HealthStatus
    environment: str
    version: str
    checks: HealthChecks
