from datetime import datetime
from pathlib import Path
from typing import Any

from litestar.logging import LoggingConfig

from chat.config.settings import get_settings

# Module-level timestamp to ensure unique log filename
# even if configure_logging is called multiple times
timestamp = datetime.now().isoformat().replace(":", "-")
# Compatibility with Windows file naming restrictions


def configure_logging() -> LoggingConfig:
    settings = get_settings()

    chat_handlers = ["queue_listener"]
    handlers: dict[str, dict[str, Any]] = {}

    if settings.logs.file or settings.logs.level == "DEBUG":
        Path("logs").mkdir(parents=True, exist_ok=True)
        handlers["file"] = {
            "class": "logging.FileHandler",
            "filename": f"logs/{timestamp}.log",
            "level": "DEBUG",
            "formatter": "standard",
        }
        chat_handlers.append("file")

    logging_config = LoggingConfig(
        configure_root_logger=False,
        formatters={
            "standard": {
                "format": "%(levelname)s - %(asctime)s - %(name)s "
                "- %(filename)s:%(lineno)d - %(message)s"
            }
        },
        handlers=handlers,
        loggers={
            "chat": {
                "level": settings.logs.level,
                "handlers": chat_handlers,
                "propagate": False,
            }
        },
    )
    return logging_config
