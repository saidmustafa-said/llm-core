import atexit
from typing import List, Optional, Dict
import re
import json
import numpy as np
import uuid
import threading
import os
from config import LLAMA_API
from src.utils import timing_decorator, extract_json_from_response

from src.data_types import TopCandidates, LocationAdviceResponse
from src.function_api_builder import build_location_request
from src.logger_setup import get_logger


# Lock for thread-safe cache operations
_cache_lock = threading.RLock()
_api_response_cache: Dict[str, any] = {}
_cache_file = "location_advice_cache.json"


def initialize_cache():
    """Initialize the cache from disk at module import time."""
    global _api_response_cache

    logger = get_logger()
    if os.path.exists(_cache_file):
        try:
            with open(_cache_file, 'r') as f:
                _api_response_cache = json.load(f)
            logger.info(
                f"Loaded {len(_api_response_cache)} cached responses from {_cache_file}")
        except Exception as e:
            logger.error(f"Error loading cache from disk: {e}")
            _api_response_cache = {}
    else:
        logger.info("No cache file found. Starting with empty cache.")
        _api_response_cache = {}


# Initialize cache when module is imported
initialize_cache()


def save_cache_to_disk():
    """Save the current cache to disk."""
    logger = get_logger()
    with _cache_lock:
        try:
            with open(_cache_file, 'w') as f:
                json.dump(_api_response_cache, f)
            logger.info(f"Cache saved to {_cache_file}")
        except Exception as e:
            logger.error(f"Error saving cache to disk: {e}")


def format_top_candidates(top_candidates: TopCandidates) -> str:
    """
    Format top candidate points of interest into a readable string.
    Handles numpy types and None values properly.
    """
    logger = get_logger()
    lines = []

    for mode, candidates in top_candidates.items():
        lines.append(f"{mode.capitalize()} Mode:")

        if candidates and len(candidates) > 0:
            for poi in candidates:
                details = [f"Mode: {mode.capitalize()}"]

                for key, value in poi.items():
                    # Convert numpy types to Python native types
                    if isinstance(value, np.generic):
                        value = value.item()  # Replaced np.asscalar with .item()

                    if value is None or (isinstance(value, float) and np.isnan(value)):
                        continue

                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if isinstance(sub_value, np.generic):
                                sub_value = sub_value.item()  # Replaced np.asscalar with .item()
                            if sub_value is None or (isinstance(sub_value, float) and np.isnan(sub_value)):
                                continue
                            details.append(
                                f"{sub_key.capitalize()}: {sub_value}")
                    else:
                        details.append(f"{key.capitalize()}: {value}")

                lines.append("\n".join(details))
        else:
            lines.append(
                f"No locations found within the specified route distance for {mode} mode.")

    logger.debug("Formatted top candidates: %s", "\n\n".join(lines))
    return "\n\n".join(lines) if lines else "No location data available."


def extract_content(response):
    """Extracts the JSON content from the response's 'content' field."""
    try:
        # Navigate to the content field
        content_str = response.get("choices", [{}])[0].get(
            "message", {}).get("content", "")

        # Parse the JSON
        extracted_json = json.loads(content_str)

        return extracted_json
    except (json.JSONDecodeError, IndexError, KeyError) as e:
        print(f"Error extracting content: {e}")
        return None


def cache_key(request_json: Dict) -> str:
    """Generate a cache key from the request JSON."""
    # Using the JSON string representation as a cache key
    # Sort keys to ensure consistent ordering
    return json.dumps(request_json, sort_keys=True)


@timing_decorator
def get_location_advice(prompt, history, top_candidates: TopCandidates,
                        latitude, longitude, search_radius) -> LocationAdviceResponse:
    logger = get_logger()
    """Main function to get location advice with structured response handling"""

    # Format context and history
    formatted_candidates = format_top_candidates(top_candidates)

    # Handle history - now expecting pre-formatted string
    user_history = history if history else "No previous conversation"

    logger.debug("User history: %s", user_history.replace('\n', ' || '))
    logger.debug("Formatted candidates: %s", formatted_candidates)

    # Build API request
    api_request = build_location_request(
        prompt, formatted_candidates, user_history,
        latitude, longitude, search_radius
    )
    logger.debug(
        f"API request JSON from build_location_request: {api_request}")

    # Generate a cache key for this request
    key = cache_key(api_request)

    # Thread-safe cache check
    with _cache_lock:
        if key in _api_response_cache:
            logger.info(
                "Found cached response for this request. Using cached result.")
            return _api_response_cache[key]

    try:
        # Execute API call if not in cache
        logger.info("Request not in cache. Calling LLAMA API.")
        response = LLAMA_API.run(api_request)
        logger.info("Received response from LLAMA API.")
        logger.debug(f"Response: {response.json()}")

        # Process response
        extracted_json = extract_content(response.json())

        # Store in cache for future use (thread-safe)
        with _cache_lock:
            _api_response_cache[key] = extracted_json
            # Periodically save cache to disk (every 10 new entries)
            if len(_api_response_cache) % 10 == 0:
                save_cache_to_disk()

        return extracted_json

    except Exception as e:
        logger.error("Location Advice API failed: %s", e)
        return {"error": f"Location Advice API failed: {str(e)}"}


# Register an exit handler to save cache when program exits
atexit.register(save_cache_to_disk)

# from typing import List, Optional, Dict
# import re
# import json
# import numpy as np
# import uuid
# from config import LLAMA_API
# from src.utils import timing_decorator, extract_json_from_response

# from src.data_types import TopCandidates, LocationAdviceResponse
# from src.function_api_builder import build_location_request
# from src.logger_setup import get_logger


# def format_top_candidates(top_candidates: TopCandidates) -> str:
#     """
#     Format top candidate points of interest into a readable string.
#     Handles numpy types and None values properly.
#     """
#     logger = get_logger()
#     lines = []

#     for mode, candidates in top_candidates.items():
#         lines.append(f"{mode.capitalize()} Mode:")

#         if candidates and len(candidates) > 0:
#             for poi in candidates:
#                 details = [f"Mode: {mode.capitalize()}"]

#                 for key, value in poi.items():
#                     # Convert numpy types to Python native types
#                     if isinstance(value, np.generic):
#                         value = value.item()  # Replaced np.asscalar with .item()

#                     if value is None or (isinstance(value, float) and np.isnan(value)):
#                         continue

#                     if isinstance(value, dict):
#                         for sub_key, sub_value in value.items():
#                             if isinstance(sub_value, np.generic):
#                                 sub_value = sub_value.item()  # Replaced np.asscalar with .item()
#                             if sub_value is None or (isinstance(sub_value, float) and np.isnan(sub_value)):
#                                 continue
#                             details.append(
#                                 f"{sub_key.capitalize()}: {sub_value}")
#                     else:
#                         details.append(f"{key.capitalize()}: {value}")

#                 lines.append("\n".join(details))
#         else:
#             lines.append(
#                 f"No locations found within the specified route distance for {mode} mode.")

#     logger.debug("Formatted top candidates: %s", "\n\n".join(lines))
#     return "\n\n".join(lines) if lines else "No location data available."


# def extract_content(response):
#     """Extracts the JSON content from the response's 'content' field."""
#     try:
#         # Navigate to the content field
#         content_str = response.get("choices", [{}])[0].get(
#             "message", {}).get("content", "")

#         # Parse the JSON
#         extracted_json = json.loads(content_str)

#         return extracted_json
#     except (json.JSONDecodeError, IndexError, KeyError) as e:
#         print(f"Error extracting content: {e}")
#         return None


# @timing_decorator
# def get_location_advice(prompt, history, top_candidates: TopCandidates,
#                         latitude, longitude, search_radius) -> LocationAdviceResponse:
#     logger = get_logger()
#     """Main function to get location advice with structured response handling"""

#     # Format context and history
#     formatted_candidates = format_top_candidates(top_candidates)

#     # Handle history - now expecting pre-formatted string
#     user_history = history if history else "No previous conversation"

#     logger.debug("User history: %s", user_history.replace('\n', ' || '))
#     logger.debug("Formatted candidates: %s", formatted_candidates)

#     # Build API request
#     api_request = build_location_request(
#         prompt, formatted_candidates, user_history,
#         latitude, longitude, search_radius
#     )
#     logger.debug(
#         f"API request JSON from build_location_request: {api_request}")

#     try:
#         # Execute API call
#         response = LLAMA_API.run(api_request)
#         logger.info("Received response from LLAMA API.")
#         logger.debug(f"Response: {response.json()}")

#         # Process response
#         extracted_json = extract_content(response.json())

#     except Exception as e:
#         logger.error("Location Advice API failed: %s", e)

#     logger.debug("API response processed with result: %s", extracted_json)

#     return extracted_json
