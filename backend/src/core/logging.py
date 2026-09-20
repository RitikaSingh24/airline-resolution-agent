"""Application logging configuration."""

import logging
import sys

from core.config import settings

logger = logging.getLogger("airline_resolution")


def setup_logging() -> None:
    """Configures application-wide logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger.info("Application logging initialized.")

    if not settings.has_llm_key():
        logger.warning(
            "LLM API key is not configured. The application will run with the stub/fallback agent."
        )
    else:
        logger.info("LLM API key detected.")
