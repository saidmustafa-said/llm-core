import logging
import functools
import re
import json
import time
from src.logger_setup import get_logger


def timing_decorator(func):
    def wrapper(*args, **kwargs):
        logger = get_logger()
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.debug(
            f"{func.__name__} execution time: {end_time - start_time:.4f} seconds")
        return result
    return wrapper


def log_io(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger()
        logger = logging.getLogger(func.__module__)
        logger.info(f"INPUT to {func.__name__}: args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        logger.info(f"OUTPUT from {func.__name__}: {result}")
        return result
    return wrapper
