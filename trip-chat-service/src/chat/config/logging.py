from datetime import datetime
from logging import config
from pathlib import Path

from chat.config.settings import get_settings

# Module-level timestamp to ensure unique log filename
# even if configure_logging is called multiple times
timestamp = datetime.now().isoformat().replace(":", "-")
# Compatibility with Windows file naming restrictions


def config_logging() -> None:
    settings = get_settings()

    logger_handlers = ["console"]
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "level": settings.log.level,
            "formatter": "standard",
        }
    }

    if settings.log.file or settings.log.level == "DEBUG":
        Path("logs").mkdir(parents=True, exist_ok=True)
        handlers["file"] = {
            "class": "logging.FileHandler",
            "filename": f"logs/{timestamp}.log",
            "level": "DEBUG",
            "formatter": "standard",
            "encoding": "utf-8",
        }
        logger_handlers.append("file")

    logging_config = {
        "version": 1,
        "formatters": {
            "standard": {
                "format": "%(levelname)s - %(asctime)s - %(name)s "
                "- %(filename)s:%(lineno)d - %(message)s"
            }
        },
        "handlers": handlers,
        "loggers": {
            "chat": {
                "level": settings.log.level,
                "handlers": logger_handlers,
                "propagate": False,
            }
        },
    }
    config.dictConfig(logging_config)
