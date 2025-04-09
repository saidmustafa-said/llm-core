
import os
import pandas as pd
from config import LLAMA_API, TAGS_LIST, CATEGORY_SUBCATEGORY_LIST
from src.utils import timing_decorator
from src.data_types import LLMResponse
from typing import List, Optional
from src.function_api_builder import create_classification_request
from src.logger_setup import get_logger
import json


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


@timing_decorator
def llm_api(prompt: str, subcategories) -> LLMResponse:
    logger = get_logger()
    logger.info("Calling LLM API with the provided prompt.")

    # user_history = history if history else "No previous conversation"
    existing_subcategories_str = subcategories
    print(existing_subcategories_str)

    logger.debug(f"Existing subcategories: {existing_subcategories_str}")
    # logger.debug("User history: %s", user_history.replace('\n', ' || '))

    # Prepare the API request
    api_request_json = create_classification_request(
        prompt, existing_subcategories_str, )
    logger.debug(
        f"API request JSON from create_classification_request: {api_request_json}")

    # Call the LLAMA API
    try:
        response = LLAMA_API.run(api_request_json)
        print("Response from LLAMA API:", response.json())
        logger.info("Received response from LLAMA API.")
        logger.debug(f"Response: {response.json()}")
    except Exception as e:
        logger.error(f"Error calling LLAMA API: {e}")
        return LLMResponse({"error": "Failed to call LLAMA API"})

    # Extract and parse JSON from the response
    extracted_json = extract_content(response.json())

    return extracted_json
