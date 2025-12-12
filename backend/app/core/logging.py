import logging
import sys

from app.core.config import get_settings

settings = get_settings()


class InterceptHandler(logging.Handler):
    """
    Default handler from examples in loguru/structlog docs
    that intercepts standard logging messages (if we strictly needed to).
    For now, we just stick to standard logging dictConfig for simplicity.
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        logger = logging.getLogger("uvicorn.error")  # Fallback or use specific logger
        level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore
            depth += 1

        logger.log(level, record.getMessage())


def setup_logging() -> None:
    """
    Configure logging for the application.
    """
    log_level = "DEBUG" if settings.debug else "INFO"
    logging_format = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"

    logging.basicConfig(
        level=log_level,
        format=logging_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # Overwrite any existing config
    )

    # Set third-party logs to warning to avoid noise
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
