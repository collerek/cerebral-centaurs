"""Main project package"""
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "default": {
            "format": "%(asctime)s:%(name)s:%(lineno)d %(levelname)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "verbose_output": {
            "formatter": "default",
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "codejam": {
            "level": "DEBUG",
            "handlers": [
                "verbose_output",
            ],
        },
    },
}
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
