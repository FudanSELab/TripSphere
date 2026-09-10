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
                },
                "otel": {
                    "class": "opentelemetry.sdk._logs.LoggingHandler",
                    "level": "NOTSET",
                }
            },
            "loggers": {
                "order_assistant": {
                    "level": settings.log.level,
                    "handlers": ["console", "otel"],
                    "propagate": False,
                },
                "starlette": {
                    "level": "INFO",
                    "handlers": ["console", "otel"],
                    "propagate": False,
                },
                "uvicorn": {
                    "level": "INFO",
                    "handlers": ["console", "otel"],
                    "propagate": False,
                },
                "uvicorn.error": {
                    "level": "INFO",
                    "handlers": ["console", "otel"],
                    "propagate": False,
                },
                "uvicorn.access": {
                    "level": "INFO",
                    "handlers": ["console", "otel"],
                    "propagate": False,
                },
            },
        }
    )
