import logging
import functools
import re
import json
import time
import math
import numpy as np
import pandas as pd
from src.core.logger_setup import get_logger
from typing import Any, Dict, List, Union


def convert_nan_to_none(obj: Any) -> Any:
    """
    Recursively convert NaN values to None in nested data structures.
    This function handles dictionaries, lists, numpy arrays, pandas Series, and DataFrames.

    Args:
        obj: The object to process

    Returns:
        The object with NaN values converted to None
    """
    if isinstance(obj, dict):
        return {k: convert_nan_to_none(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_nan_to_none(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        return convert_nan_to_none(obj.tolist())
    elif isinstance(obj, pd.Series):
        return convert_nan_to_none(obj.to_dict())
    elif isinstance(obj, pd.DataFrame):
        return convert_nan_to_none(obj.to_dict(orient='records'))
    elif isinstance(obj, float) and (math.isnan(obj) or pd.isna(obj)):
        return None
    else:
        return obj


def serialize_for_json(obj: Any) -> Any:
    """
    Prepare an object for JSON serialization by converting non-serializable types.

    Args:
        obj: The object to serialize

    Returns:
        A JSON-serializable version of the object
    """
    # First convert NaN values to None
    obj = convert_nan_to_none(obj)

    # Handle numpy types
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, pd.Series):
        return obj.to_dict()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    else:
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
