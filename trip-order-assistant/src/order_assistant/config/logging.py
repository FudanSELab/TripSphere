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
                    "- %(filename)s:%(lineno)d - request_id=%(request_id)s - %(message)s"
                }
            },
            "filters": {
                "correlation": {
                    "()": "order_assistant.tools.context.CorrelationLogFilter"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "stream": "ext://sys.stderr",
                    "filters": ["correlation"],
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
                    "handlers": ["console"],
                    "propagate": True,
                },
                "uvicorn": {
                    "level": "INFO",
                    "handlers": ["console"],
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
