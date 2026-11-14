from enum import StrEnum

from pydantic import BaseModel


class HealthStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"


class CheckStatus(StrEnum):
    OK = "ok"
    ERROR = "error"


class LLMStatus(StrEnum):
    OK = "ok"
    UNAVAILABLE = "unavailable"


class LLMCheck(BaseModel):
    status: LLMStatus
    provider: str


class HealthChecks(BaseModel):
    database: CheckStatus
    # Informational: the application works without the LLM, only chat does not.
    llm: LLMCheck


class HealthResponse(BaseModel):
    status: HealthStatus
    environment: str
    version: str
    checks: HealthChecks
