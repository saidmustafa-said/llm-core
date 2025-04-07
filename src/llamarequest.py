import atexit
import os
import pandas as pd
import json
import threading
import time
from functools import lru_cache
from config import LLAMA_API, TAGS_LIST, CATEGORY_SUBCATEGORY_LIST
from src.utils import timing_decorator, extract_json_from_response
from src.data_types import LLMResponse
from typing import List, Optional, Dict, Any
from src.function_api_builder import create_classification_request
from src.logger_setup import get_logger


# Lock for thread-safe cache operations
_cache_lock = threading.RLock()
_api_response_cache: Dict[str, Any] = {}
_cache_file = "api_response_cache.json"


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


@timing_decorator
def retrieve_tags():
    logger = get_logger()
    logger.info("Retrieving tags and subcategories from CSV files.")

    tags_string, subcategory_string = "None", "None"

    # Check if the tags list file exists and process it
    if os.path.exists(TAGS_LIST):
        logger.debug(f"Reading tags from file: {TAGS_LIST}")
        try:
            tags_df = pd.read_csv(TAGS_LIST)
            if 'tags' in tags_df.columns:
                tags_list = tags_df['tags'].dropna().tolist()
                tags_string = ", ".join(tags_list) if tags_list else "None"
                logger.info(f"Tags retrieved: {tags_string}")
        except Exception as e:
            logger.error(f"Error reading tags from {TAGS_LIST}: {e}")

    # Check if the category and subcategory list file exists and process it
    if os.path.exists(CATEGORY_SUBCATEGORY_LIST):
        logger.debug(
            f"Reading subcategories from file: {CATEGORY_SUBCATEGORY_LIST}")
        try:
            subcategory_df = pd.read_csv(CATEGORY_SUBCATEGORY_LIST)
            if 'category' in subcategory_df.columns and 'subcategory' in subcategory_df.columns:
                grouped = subcategory_df.groupby('category')['subcategory'].apply(
                    lambda x: ",".join(x)).reset_index()
                subcategory_string = "\n".join(
                    [f"{row['category']}: {row['subcategory']}" for _, row in grouped.iterrows()])
                subcategory_string = subcategory_string if subcategory_string else "None"
        except Exception as e:
            logger.error(
                f"Error reading subcategories from {CATEGORY_SUBCATEGORY_LIST}: {e}")

    return tags_string, subcategory_string


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
def llm_api(prompt: str, history, subcategories) -> LLMResponse:
    logger = get_logger()
    logger.info("Calling LLM API with the provided prompt.")

    existing_tags_str, existing_subcategories_str = retrieve_tags()
    user_history = history if history else "No previous conversation"
    existing_subcategories_str = subcategories
    print(existing_subcategories_str)

    logger.debug(f"Existing tags: {existing_tags_str}")
    logger.debug(f"Existing subcategories: {existing_subcategories_str}")
    logger.debug("User history: %s", user_history.replace('\n', ' || '))

    # Prepare the API request
    api_request_json = create_classification_request(
        prompt, user_history, existing_subcategories_str, existing_tags_str)
    logger.debug(
        f"API request JSON from create_classification_request: {api_request_json}")

    # Generate a cache key for this request
    key = cache_key(api_request_json)

    # Thread-safe cache check
    with _cache_lock:
        if key in _api_response_cache:
            logger.info(
                "Found cached response for this request. Using cached result.")
            return _api_response_cache[key]

    # Call the LLAMA API if not in cache
    try:
        logger.info("Request not in cache. Calling LLAMA API.")
        response = LLAMA_API.run(api_request_json)
        logger.info("Received response from LLAMA API.")
        logger.debug(f"Response: {response.json()}")

        # Extract and parse JSON from the response
        extracted_json = extract_content(response.json())

        # Store in cache for future use (thread-safe)
        with _cache_lock:
            _api_response_cache[key] = extracted_json
            # Periodically save cache to disk (every 10 new entries)
            if len(_api_response_cache) % 10 == 0:
                save_cache_to_disk()

        return extracted_json
    except Exception as e:
        logger.error(f"Error calling LLAMA API: {e}")
        return LLMResponse({"error": "Failed to call LLAMA API"})


# Register an exit handler to save cache when program exits
atexit.register(save_cache_to_disk)

# import os
# import pandas as pd
# from config import LLAMA_API, TAGS_LIST, CATEGORY_SUBCATEGORY_LIST
# from src.utils import timing_decorator, extract_json_from_response
# from src.data_types import LLMResponse
# from typing import List, Optional
# from src.function_api_builder import create_classification_request
# from src.logger_setup import get_logger
# import json


# @timing_decorator
# def retrieve_tags():
#     logger = get_logger()
#     logger.info("Retrieving tags and subcategories from CSV files.")

#     tags_string, subcategory_string = "None", "None"

#     # Check if the tags list file exists and process it
#     if os.path.exists(TAGS_LIST):
#         logger.debug(f"Reading tags from file: {TAGS_LIST}")
#         try:
#             tags_df = pd.read_csv(TAGS_LIST)
#             if 'tags' in tags_df.columns:
#                 tags_list = tags_df['tags'].dropna().tolist()
#                 tags_string = ", ".join(tags_list) if tags_list else "None"
#                 logger.info(f"Tags retrieved: {tags_string}")
#         except Exception as e:
#             logger.error(f"Error reading tags from {TAGS_LIST}: {e}")

#     # Check if the category and subcategory list file exists and process it
#     if os.path.exists(CATEGORY_SUBCATEGORY_LIST):
#         logger.debug(
#             f"Reading subcategories from file: {CATEGORY_SUBCATEGORY_LIST}")
#         try:
#             subcategory_df = pd.read_csv(CATEGORY_SUBCATEGORY_LIST)
#             if 'category' in subcategory_df.columns and 'subcategory' in subcategory_df.columns:
#                 grouped = subcategory_df.groupby('category')['subcategory'].apply(
#                     lambda x: ",".join(x)).reset_index()
#                 subcategory_string = "\n".join(
#                     [f"{row['category']}: {row['subcategory']}" for _, row in grouped.iterrows()])
#                 subcategory_string = subcategory_string if subcategory_string else "None"
#                 # logger.info(f"Subcategories retrieved: {subcategory_string}")
#         except Exception as e:
#             logger.error(
#                 f"Error reading subcategories from {CATEGORY_SUBCATEGORY_LIST}: {e}")

#     return tags_string, subcategory_string


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
# def llm_api(prompt: str, history, subcategories) -> LLMResponse:
#     logger = get_logger()
#     logger.info("Calling LLM API with the provided prompt.")

#     existing_tags_str, existing_subcategories_str = retrieve_tags()
#     user_history = history if history else "No previous conversation"
#     existing_subcategories_str = subcategories
#     print(existing_subcategories_str)

#     logger.debug(f"Existing tags: {existing_tags_str}")
#     logger.debug(f"Existing subcategories: {existing_subcategories_str}")
#     logger.debug("User history: %s", user_history.replace('\n', ' || '))

#     # Prepare the API request
#     api_request_json = create_classification_request(
#         prompt, user_history, existing_subcategories_str, existing_tags_str, )
#     logger.debug(
#         f"API request JSON from create_classification_request: {api_request_json}")

#     # Call the LLAMA API
#     try:
#         response = LLAMA_API.run(api_request_json)
#         logger.info("Received response from LLAMA API.")
#         logger.debug(f"Response: {response.json()}")
#     except Exception as e:
#         logger.error(f"Error calling LLAMA API: {e}")
#         return LLMResponse({"error": "Failed to call LLAMA API"})

#     # Extract and parse JSON from the response
#     extracted_json = extract_content(response.json())

#     return extracted_json
