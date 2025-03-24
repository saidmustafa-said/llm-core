import re
import json
import time
from src.logger_setup import logger_instance


def timing_decorator(func):
    def wrapper(*args, **kwargs):
        logger = logger_instance.get_logger()
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.debug(
            f"{func.__name__} execution time: {end_time - start_time:.4f} seconds")
        return result
    return wrapper


def extract_json_from_response(response):
    """
    Extract JSON content from the response using multiple methods: direct parsing and regex extraction.
    This function attempts to parse the JSON directly, and if it fails, it falls back to using a regex to extract a valid JSON string.
    """
    logger = logger_instance.get_logger()
    logger.info("Extracting JSON content from the response.")

    # Try direct JSON parsing
    try:
        content = response.json()['choices'][0]['message']['content']
        logger.debug(f"Response JSON content: {content}")
    except Exception as e:
        logger.error(f"Error extracting content from response: {e}")
        return {}

    # Try direct JSON parsing
    try:
        result = json.loads(content)
        logger.info("Direct JSON parsing successful.")
        return result
    except json.JSONDecodeError:
        logger.warning(
            "Direct JSON parsing failed. Trying regex extraction...")

    # Regex extraction as a fallback
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        json_str = match.group(0).strip()
        try:
            result = json.loads(json_str)
            logger.info("Regex JSON extraction successful.")
            return result
        except json.JSONDecodeError:
            logger.error("Regex JSON extraction failed.")

    logger.error("No valid JSON found in response content.")
    return {}
