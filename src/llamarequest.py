import os
import time
import uuid
import json
import re
import pandas as pd
import logging
from src.history_manager import HistoryManager
from config import LLAMA_API, TAGS_LIST, CATEGORY_SUBCATEGORY_LIST
from src.utils import count_tokens, timing_decorator
from src.data_types import LLMResponse
from typing import List, Optional

import os
import logging
from datetime import datetime


def setup_logging(script_name: str) -> logging.Logger:
    """
    Set up logging to create a unique log file based on the script name and timestamp.

    Parameters:
    - script_name: Name of the script (used to create the log folder).

    Returns:
    - logger: Configured logger instance.
    """
    # Create the log directory based on the script name
    log_directory = f'logs/{script_name}'
    os.makedirs(log_directory, exist_ok=True)

    # Generate a unique log filename based on the current timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_filename = os.path.join(log_directory, f"log_{timestamp}.log")

    # Set up logging to both the console and the log file
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),  # Log to the generated log file
            logging.StreamHandler()  # Also log to the console
        ]
    )

    # Return the logger instance
    return logging.getLogger(script_name)


# Get the script name (without the .py extension) to pass to the logging setup
script_name = os.path.splitext(os.path.basename(__file__))[0]

# Set up logging using the script name
logger = setup_logging(script_name)

# Now you can use the logger as usual
logger.info("This is an informational message.")


@timing_decorator
def retrieve_tags():
    """
    Retrieves tags and subcategories from CSV files and returns them as formatted strings.
    """
    tags_string = "None"
    subcategory_string = "None"

    # Retrieve tags
    if os.path.exists(TAGS_LIST):
        tags_df = pd.read_csv(TAGS_LIST)
        if 'tags' in tags_df.columns:
            tags_list = tags_df['tags'].dropna().tolist()
            tags_string = ", ".join(tags_list) if tags_list else "None"

    # Retrieve subcategories
    if os.path.exists(CATEGORY_SUBCATEGORY_LIST):
        subcategory_df = pd.read_csv(CATEGORY_SUBCATEGORY_LIST)
        if 'category' in subcategory_df.columns and 'subcategory' in subcategory_df.columns:
            grouped = subcategory_df.groupby('category')['subcategory'].apply(
                lambda x: ",".join(x)).reset_index()
            subcategory_string = "\n".join(
                [f"{row['category']}: {row['subcategory']}" for _, row in grouped.iterrows()])
            subcategory_string = subcategory_string if subcategory_string else "None"

    return tags_string, subcategory_string


@timing_decorator
def extract_json(response):
    """
    Extract JSON from the API response using direct parsing and fallback to regex.
    """
    try:
        content = response.json()['choices'][0]['message']['content']
    except Exception as e:
        logger.error("Error parsing response JSON: %s", e)
        return {}
    try:
        result = json.loads(content)
        logger.info("Direct JSON parsing successful.")
        return result
    except json.JSONDecodeError:
        logger.warning(
            "Direct JSON parsing failed. Trying regex extraction...")
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        json_str = match.group(0).strip()
        try:
            result = json.loads(json_str)
            logger.info("Regex JSON extraction successful.")
            return result
        except json.JSONDecodeError:
            logger.error("Regex JSON extraction also failed.")
    logger.error("No valid JSON found.")
    return {}


def save_request_data(conversation_id, request_type, prompt, context, system_content, response, token_counts):
    """
    Save request and response data to a JSON file for logging/debugging purposes.
    """
    os.makedirs("requests", exist_ok=True)
    timestamp = int(time.time())
    filename = f"requests/{conversation_id}_{request_type}_{timestamp}.json"
    data = {
        "conversation_id": conversation_id,
        "request_type": request_type,
        "timestamp": timestamp,
        "prompt": prompt,
        "context": context,
        "system_content": system_content,
        "response": response,
        "token_counts": token_counts
    }
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info("Request saved to %s", filename)
    except Exception as e:
        logger.error("Error saving request data: %s", e)


def build_api_request(prompt: str, user_context: str, existing_subcategories: str, existing_tags: str, system_overview: str) -> dict:
    """
    Build the API request payload.
    """
    system_content = (
        "You are an AI specializing in location classification. "
        f"Existing subcategories: {existing_subcategories}. "
        f"Existing descriptive tags: {existing_tags}. "
        f"User conversation history: {user_context}. "
        f"{system_overview} "
        "Analyze the user's prompt to determine which subcategories (only subcategory names, not categories) it fits into and which descriptive tags apply. "
        "Return the matching subcategories and descriptive tags. "
        "If the prompt does not exactly match any existing tag, generate new ones that better capture its essence. "
        "Return both subcategories and descriptive tags. "
        "If multiple valid subcategories exist and the intent is unclear, return a clarification question."
    )
    return {
        "model": "llama3.1-70b",
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": f"Analyze this prompt: '{prompt}'"}
        ],
        "functions": [
            {
                "name": "extract_location_info",
                "description": (
                    "Extract the most relevant subcategories and descriptive tags from the user's prompt based on the provided context. "
                    "For subcategories, compare the prompt with the existing list and return the relevant matches. "
                    "For descriptive tags, do the same by returning matched tags or generating new descriptive words that capture the location's nuances. "
                    "Ensure both subcategories and tags are unique, non-redundant, and appropriately capture the nuances of the location described in the prompt. "
                    "If multiple subcategories are found and the intent is unclear, generate a clarification question."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subcategories": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of top 3 matching subcategories."
                        },
                        "tags": {
                            "type": "object",
                            "properties": {
                                "existed": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Top 3 descriptive tags that match existing ones."
                                },
                                "new": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "New descriptive tags generated from the prompt."
                                }
                            },
                            "required": ["existed", "new"]
                        },
                        "clarification": {
                            "type": "object",
                            "properties": {
                                "needed": {
                                    "type": "boolean",
                                    "description": "True if clarification is needed, False if the classification is certain."
                                },
                                "question": {
                                    "type": "string",
                                    "description": "Clarification question to ask the user if needed."
                                }
                            },
                            "required": ["needed", "question"]
                        }
                    },
                    "required": ["subcategories", "tags", "clarification"]
                }
            }
        ],
        "function_call": "extract_location_info",
        "max_tokens": 5000,
        "temperature": 0.2,
    }


@timing_decorator
def llm_api(prompt: str, user_context: Optional[List[str]] = None,
            conversation_id: Optional[str] = None,
            history_manager: Optional[HistoryManager] = None) -> LLMResponse:
    """
    LLM API function that prepares the request, sends it to the LLAMA_API, processes the response,
    and saves the complete interaction to history.
    """

    existing_tags_str, existing_subcategories_str = retrieve_tags()
    user_history = "\n".join(user_context) if user_context else "None"
    system_overview = ""  # Add additional system instructions if needed

    api_request_json = build_api_request(
        prompt, user_history, existing_subcategories_str, existing_tags_str, system_overview)
    input_tokens = count_tokens(
        api_request_json["messages"][0]["content"]) + count_tokens(prompt)
    response = LLAMA_API.run(api_request_json)
    response_data = response.json()
    try:
        response_content = response_data['choices'][0]['message']['content']
    except Exception as e:
        logger.error("Error extracting response content: %s", e)
        response_content = ""
    output_tokens = count_tokens(response_content)
    total_tokens = input_tokens + output_tokens
    token_counts = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens
    }

    parsed_json = extract_json(response)
    if parsed_json:
        clarification_question = parsed_json.get('clarification', {}).get(
            'question') if parsed_json.get('clarification', {}).get('needed') else None
        categories = parsed_json.get('subcategories', [])
        tags = parsed_json.get('tags', {}).get('existed', [])
        result = {
            "clarification": clarification_question,
            "categories": categories,
            "tags": tags
        }
    else:
        result = {"error": "Failed to extract JSON"}

    request_data = {
        "request_type": "llm_classification",
        "timestamp": int(time.time()),
        "prompt": prompt,
        "context": user_context,
        "system_content": api_request_json["messages"][0]["content"],
        "api_request": api_request_json,
        "api_response": response_data,
        "token_counts": token_counts
    }

    if result.get("clarification"):
        history_manager.add_llm_interaction(
            conversation_id=conversation_id,
            response=result,
            request_data=request_data
        )
    save_request_data(conversation_id,
                      "llm_classification",
                      prompt, user_context,
                      api_request_json["messages"][0]["content"],
                      response_data,
                      token_counts)
    return LLMResponse(result)
