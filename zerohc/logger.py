"""LOGGER
Logger instance
"""

# # Native # #
import sys

# # Installed # #
import loguru
# noinspection PyProtectedMember
from loguru._logger import Logger

__all__ = ("logger", "Logger", "LoggerServices", "setup_logger")


class LoggerServices:
    Hearth = "hearth"
    Stethoscope = "stethoscope"


class LoggerFormats(LoggerServices):
    Hearth = "<green>{time:YY-MM-DD HH:mm:ss}</green> | " \
             "[<fg #ff00ff>{extra[service]}</fg #ff00ff> <level>{level}]</level> | " \
             "<fg #ff00ff>{message}</fg #ff00ff>"
    Stethoscope = "<green>{time:YY-MM-DD HH:mm:ss}</green> | " \
                  "[<fg #ffa500>{extra[service]}</fg #ffa500> <level>{level}]</level> | " \
                  "{extra[host]}: <fg #ffa500>{message}</fg #ffa500>"


def setup_logger(level):
    """Setup the logger with the given level and return it"""
    logger = loguru.logger
    logger.remove()

    # Hearth logger
    logger.add(
        sys.stdout,
        level=level,
        filter=lambda record: record["extra"].get("service") == LoggerServices.Hearth,
        format=LoggerFormats.Hearth
    )

    # Stethoscope logger
    logger.add(
        sys.stdout,
        level=level,
        filter=lambda record: record["extra"].get("service") == LoggerServices.Stethoscope,
        format=LoggerFormats.Stethoscope
    )

    return logger
