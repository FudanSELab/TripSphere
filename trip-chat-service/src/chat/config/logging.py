from datetime import datetime
from logging import config
from pathlib import Path

from chat.config.settings import get_settings
from chat.correlation import RequestIdLogFilter

# Module-level timestamp to ensure unique log filename
# even if configure_logging is called multiple times
timestamp = datetime.now().isoformat().replace(":", "-")
# Compatibility with Windows file naming restrictions


def setup_logging() -> None:
    settings = get_settings()

    logger_handlers: list[str] = ["console"]
    handlers: dict[str, dict[str, object]] = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "filters": ["request_id"],
            "stream": "ext://sys.stderr",
        }
    }

    if settings.log.file or settings.log.level == "DEBUG":
        Path("logs").mkdir(parents=True, exist_ok=True)
        handlers["file"] = {
            "class": "logging.FileHandler",
            "filename": f"logs/{timestamp}.log",
            "level": "DEBUG",
            "formatter": "standard",
            "filters": ["request_id"],
            "encoding": "utf-8",
        }
        logger_handlers.append("file")

    logging_config: dict[str, object] = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_id": {
                "()": RequestIdLogFilter,
            }
        },
        "formatters": {
            "standard": {
                "format": "%(levelname)s - %(asctime)s - %(name)s "
                "- %(filename)s:%(lineno)d - request_id=%(request_id)s - %(message)s"
            }
        },
        "handlers": handlers,
        "loggers": {
            "chat": {
                "level": settings.log.level,
                "handlers": logger_handlers,
                "propagate": True,
            },
            "fastapi": {
                "level": "INFO",
                "handlers": logger_handlers,
                "propagate": True,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": logger_handlers,
                "propagate": True,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": [],
                "propagate": True,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": [],
                "propagate": True,
            },
        },
    }
    config.dictConfig(logging_config)
