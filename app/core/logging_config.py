import logging.config
import structlog
from zoneinfo import ZoneInfo
from datetime import datetime

IST = ZoneInfo("Asia/Kolkata")


def ist_timestamper(logger, name, event_dict):
    event_dict["timestamp"] = datetime.now(IST).isoformat()
    return event_dict


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structlog": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
            "foreign_pre_chain": [
                ist_timestamper,
                structlog.stdlib.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
            ],
        },
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "structlog",
        },
    },
    "root": {
        "handlers": ["default"],
        "level": "INFO",
    },
}


def configure_logging():
    logging.config.dictConfig(LOGGING_CONFIG)
    structlog.configure(
        processors=[
            ist_timestamper,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
