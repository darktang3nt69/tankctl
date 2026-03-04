"""
TankCtl Backend Main Entry Point.

Runs the FastAPI application with uvicorn.
All initialization (database, MQTT, scheduler) is handled by
the API lifespan context manager in src/api/main.py.
"""

import sys

from src.config.settings import settings
from src.api.main import app
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Start TankCtl backend."""
    import uvicorn
    
    logger.info(
        "tankctl_starting",
        host=settings.api.host,
        port=settings.api.port,
        debug=settings.api.debug,
    )
    
    try:
        uvicorn.run(
            app,
            host=settings.api.host,
            port=settings.api.port,
            debug=settings.api.debug,
            log_level=settings.log_level.lower(),
        )
    except KeyboardInterrupt:
        logger.info("tankctl_shutdown_by_user")
        sys.exit(0)
    except Exception as e:
        logger.error("tankctl_startup_error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
