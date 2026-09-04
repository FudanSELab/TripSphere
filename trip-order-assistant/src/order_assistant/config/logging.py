from datetime import datetime
from logging import Filter, LogRecord
from logging import config
from pathlib import Path

from order_assistant.config.settings import get_settings

timestamp = datetime.now().isoformat().replace(":", "-")


class TraceContextFilter(Filter):
    def filter(self, record: LogRecord) -> bool:
        setattr(record, "otelTraceID", getattr(record, "otelTraceID", "0"))
        setattr(record, "otelSpanID", getattr(record, "otelSpanID", "0"))
        return True


def setup_logging() -> None:
    settings = get_settings()
    logger_handlers = ["console"]
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "filters": ["trace_context"],
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
            "filters": ["trace_context"],
            "encoding": "utf-8",
        }
        logger_handlers.append("file")

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"trace_context": {"()": TraceContextFilter}},
        "formatters": {
            "standard": {
                "format": "level=%(levelname)s timestamp=%(asctime)s "
                "service=trip-order-assistant trace_id=%(otelTraceID)s "
                "span_id=%(otelSpanID)s logger=%(name)s "
                "source=%(filename)s:%(lineno)d message=%(message)s"
            }
        },
        "handlers": handlers,
        "loggers": {
            "order_assistant": {
                "level": settings.log.level,
                "handlers": logger_handlers,
                "propagate": False,
            }
        },
    }
    config.dictConfig(logging_config)
