import logging
import logging.config
from pathlib import Path

# Create logs directory if it does not exist
Path("logs").mkdir(parents=True, exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "formatter": "standard",
            "class": "logging.StreamHandler",
        },
        "file": {
            "level": "INFO",
            "formatter": "json",
            "class": "logging.FileHandler",
            "filename": "logs/application.log",
        },
        "error_file": {
            "level": "ERROR",
            "formatter": "json",
            "class": "logging.FileHandler",
            "filename": "logs/errors.log",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "file", "error_file"],
            "level": "DEBUG",
            "propagate": True,
        },
        "uvicorn.access": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["console", "error_file"],
            "level": "ERROR",
            "propagate": True,
        },
        "pymongo": {  # Add a separate logger for pymongo
            "handlers": ["console"],
            "level": "WARNING",  # Set the level to WARNING to suppress DEBUG logs
            "propagate": False,
        },
    },
}

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(level=logging.WARNING)
    logging.config.dictConfig(LOGGING_CONFIG)
