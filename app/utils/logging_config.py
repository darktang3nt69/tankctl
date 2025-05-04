# app/core/logging_config.py

import logging
from pytz import timezone
from datetime import datetime

IST = timezone("Asia/Kolkata")

class ISTFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, IST)
        return dt.strftime(datefmt or "%Y-%m-%d %H:%M:%S")

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": ISTFormatter,
            "fmt": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        # ❗ Use only %(asctime)s + %s placeholders, not named fields for access logs
        "access": {
            "()": ISTFormatter,
            "fmt": "[%(asctime)s] %s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["default"],
            "level": "INFO",
        },
        "uvicorn.access": {
            "handlers": ["access"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
