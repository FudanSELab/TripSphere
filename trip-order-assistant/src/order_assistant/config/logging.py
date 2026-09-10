from logging import config

from order_assistant.config.settings import get_settings


def setup_logging() -> None:
    settings = get_settings()
    config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(levelname)s - %(asctime)s - %(name)s "
                    "- %(filename)s:%(lineno)d - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "stream": "ext://sys.stderr",
                }
            },
            "loggers": {
                "order_assistant": {
                    "level": settings.log.level,
                    "handlers": ["console"],
                    "propagate": True,
                },
                "starlette": {
                    "level": "INFO",
                    "handlers": [],
                    "propagate": True,
                },
                "uvicorn": {
                    "level": "INFO",
                    "handlers": [],
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
    )
