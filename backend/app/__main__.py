"""Start the API server with the address from the settings.

Run with: ``uv run python -m app``
"""

import uvicorn

from app.core.config import AppEnvironment, get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host=settings.api_host,
        port=settings.api_port,
        # Restart on code changes while developing.
        reload=settings.app_env is AppEnvironment.DEVELOPMENT,
    )


if __name__ == "__main__":
    main()
