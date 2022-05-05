#!/usr/bin/env python3
"""
Description
-----------
Sets up a standardized method for logging to stdout.
"""
import json
import logging
import sys


class FilterNoQuotes(logging.Filter):
    """Hack to get a somewhat reliable JSON output without much effort"""

    def filter(self, record):
        record.msg = json.dumps(
            record.msg,
            # Ah, so you want to throw a datetime in there do ya smart ass?
            # Well guess what, it's a string now.
            default=str,
        )
        return record


def get_logger(name: str = "coinbase", level: int = logging.INFO) -> logging.Logger:
    """
    Description
    -----------
    Meant to be kind of like the regular getLogger() function, but with a
    custom formatter so that the logs produced are all in JSON format.
    \U0001F60E

    Params
    ------
    :name: str = "coinbase"
    The name for the logger, it will appear in every single log entry so your
    poor little brain doesn't get confused about what logs you're reading.

    :level: int = logging.INFO
    The logging level, use the builtin enum for the logging levels, or be a
    jerk and have folks try to guess what `level=10` means.

    Return
    ------
    logging.Logger
    Not the logger you needed, but definitely the one you asked for.
    """
    logging.basicConfig(
        format="""{"time":"%(asctime)s","path":"%(pathname)s","name":"%(name)s","""
        + """"logLevel":"%(levelname)s","message":%(message)s}""",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        level=level,
        stream=sys.stdout,
    )
    logger = logging.getLogger(name)
    logger.addFilter(FilterNoQuotes())
    return logger


if __name__ == "__main__":
    logger = get_logger(name="test_logging")
    logger.info("Info Test")
    logger.warn("Warning Test")
    logger.error("Error Test")
    logger.critical("Critical Test")
