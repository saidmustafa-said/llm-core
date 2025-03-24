import os
import pandas as pd
from config import LLAMA_API, TAGS_LIST, CATEGORY_SUBCATEGORY_LIST
from src.utils import timing_decorator, extract_json_from_response
from src.data_types import LLMResponse
from typing import List, Optional
from src.function_api_builder import create_classification_request
from src.logger_setup import logger_instance


@timing_decorator
def retrieve_tags():
    logger = logger_instance.get_logger()
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
                logger.info(f"Subcategories retrieved: {subcategory_string}")
        except Exception as e:
            logger.error(
                f"Error reading subcategories from {CATEGORY_SUBCATEGORY_LIST}: {e}")

    return tags_string, subcategory_string


@timing_decorator
def llm_api(prompt: str, history) -> LLMResponse:
    logger = logger_instance.get_logger()
    logger.info("Calling LLM API with the provided prompt.")

    existing_tags_str, existing_subcategories_str = retrieve_tags()
    user_history = history if history else "No previous conversation"
    system_overview = ""

    logger.debug(f"Existing tags: {existing_tags_str}")
    logger.debug(f"Existing subcategories: {existing_subcategories_str}")
    logger.debug("User history: %s", user_history.replace('\n', ' || '))

    # Prepare the API request
    api_request_json = create_classification_request(
        prompt, user_history, existing_subcategories_str, existing_tags_str, system_overview)
    logger.debug(
        f"API request JSON from create_classification_request: {api_request_json}")

    # Call the LLAMA API
    try:
        response = LLAMA_API.run(api_request_json)
        logger.info("Received response from LLAMA API.")
    except Exception as e:
        logger.error(f"Error calling LLAMA API: {e}")
        return LLMResponse({"error": "Failed to call LLAMA API"})

    # Extract and parse JSON from the response
    parsed_json = extract_json_from_response(response)

    # Prepare the result
    if parsed_json:
        result = {
            "clarification": parsed_json.get('clarification', {}).get('question') if parsed_json.get('clarification', {}).get('needed') else None,
            "categories": parsed_json.get('subcategories', []),
            "tags": parsed_json.get('tags', {}).get('existed', [])
        }
        logger.info(f"API result: {result}")
    else:
        result = {"error": "Failed to extract JSON"}
        logger.error(f"Failed to extract valid JSON from the response.")

    return LLMResponse(result)
