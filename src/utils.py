import logging
import functools
import re
import json
import time
import math
from src.logger_setup import get_logger


def convert_nan_to_none(obj):
    """
    Recursively convert NaN values to None in a dictionary or list.

    Args:
        obj: The object to process (dict, list, or other)

    Returns:
        The processed object with NaN values replaced by None
    """
    if isinstance(obj, dict):
        return {k: convert_nan_to_none(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_nan_to_none(item) for item in obj]
    elif isinstance(obj, float) and math.isnan(obj):
        return None
    return obj


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
