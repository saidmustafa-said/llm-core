import os
import time
import json
import re
import pandas as pd
import logging
from src.history_manager import HistoryManager
from config import LLAMA_API, TAGS_LIST, CATEGORY_SUBCATEGORY_LIST
from src.utils import count_tokens, timing_decorator
from src.data_types import LLMResponse
from typing import List, Optional
from datetime import datetime
from src.function_api_builder import create_classification_request


def setup_logging(script_name: str) -> logging.Logger:
    log_directory = f'logs/{script_name}'
    os.makedirs(log_directory, exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_filename = os.path.join(log_directory, f"log_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(script_name)


script_name = os.path.splitext(os.path.basename(__file__))[0]
logger = setup_logging(script_name)


@timing_decorator
def retrieve_tags():
    tags_string = "None"
    subcategory_string = "None"

    if os.path.exists(TAGS_LIST):
        tags_df = pd.read_csv(TAGS_LIST)
        if 'tags' in tags_df.columns:
            tags_list = tags_df['tags'].dropna().tolist()
            tags_string = ", ".join(tags_list) if tags_list else "None"

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




@timing_decorator
def llm_api(prompt: str, user_context: Optional[List[str]] = None,
            conversation_id: Optional[str] = None,
            history_manager: Optional[HistoryManager] = None) -> LLMResponse:
    existing_tags_str, existing_subcategories_str = retrieve_tags()
    user_history = "\n".join(user_context) if user_context else "None"
    system_overview = ""  # Add additional system instructions if needed

    api_request_json = create_classification_request(
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
    return LLMResponse(result)
