from typing import List, Optional, Dict
import re
import json
import numpy as np
import os
import uuid
import time
import logging
from config import LLAMA_API
from src.utils import timing_decorator, count_tokens
from src.history_manager import HistoryManager
from src.data_types import TopCandidates, LocationAdviceResponse

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
def save_request_data(conversation_id, request_type, prompt, context, system_content, response, token_counts, top_candidates=None):
    """
    Save the full request/response data to a JSON file.
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
    if top_candidates:
        data["top_candidates"] = top_candidates

    try:
        with open(filename, 'w') as f:
            json.dump(data, f, default=str, indent=2)
        logger.info("Request saved to %s", filename)
    except Exception as e:
        logger.error("Error saving request data: %s", e)


@timing_decorator
def format_top_candidates(top_candidates: TopCandidates) -> str:
    """
    Format top candidate points of interest into a readable string.
    Handles numpy types and None values properly.
    """
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
    return "\n\n".join(lines) if lines else "No location data available."


@timing_decorator
def extract_location_json(response):
    """Extract JSON from location advice response using multiple methods"""
    try:
        content = response.json()['choices'][0]['message']['content']
    except Exception as e:
        logger.error("Error extracting response content: %s", e)
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

    logger.error("No valid JSON found in response content")
    return {}


def build_location_request(prompt: str, context_text: str, user_history: str,
                           latitude: float, longitude: float, search_radius: int) -> dict:
    """Build the location advice API request payload"""
    system_content = (
        "You are a friendly location recommendation assistant. "
        f"User coordinates: ({latitude}, {longitude}), Search radius: {search_radius}m\n"
        f"Conversation history:\n{user_history}\n\n"
        f"Context data:\n{context_text}\n\n"
        "Provide specific recommendations with details from the context. "
        "Include addresses and directions when available."
    )

    return {
        "model": "llama3.1-70b",
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ],
        "functions": [
            {
                "name": "analyze_location_request",
                "description": (
                    "Determines if the prompt is a continuation of the conversation or a new request. "
                    "If it's a continuation, return continuation: true. "
                    "If it's not, return continuation: false and generate a response based on context and history "
                    "to answer the user's prompt, including details like address, coordinates, and directions."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "continuation": {
                            "type": "boolean",
                            "description": "True if the query is a continuation, False if it's a new request."
                        },
                        "response": {
                            "type": "string",
                            "description": (
                                "A detailed response using the provided context to answer the user's prompt. "
                                "Include address, coordinates, and directions where available."
                            )
                        }
                    },
                    "required": ["continuation", "response"]
                }
            }
        ],
        "function_call": "analyze_location_request",
        "max_tokens": 7000,
        "temperature": 0.7
    }


@timing_decorator
def get_location_advice(prompt: str, history: List[str], top_candidates: TopCandidates,
                        latitude: float, longitude: float, search_radius: int,
                        conversation_id: Optional[str] = None,
                        history_manager: Optional[HistoryManager] = None) -> LocationAdviceResponse:
    """Main function to get location advice with structured response handling"""
    # Initialize conversation and history
    conversation_id = conversation_id or str(uuid.uuid4())
    history_manager = history_manager or HistoryManager()

    # Format context and history
    formatted_candidates = format_top_candidates(top_candidates)
    user_history = "\n".join(
        history) if history else "No previous conversation"

    # Build API request
    api_request = build_location_request(
        prompt, formatted_candidates, user_history,
        latitude, longitude, search_radius
    )

    # Track token usage
    input_tokens = count_tokens(
        api_request["messages"][0]["content"]) + count_tokens(prompt)

    try:
        # Execute API call
        response = LLAMA_API.run(api_request)
        response_data = response.json()
        response_content = response_data.get('choices', [{}])[
            0].get('message', {}).get('content', '')
        output_tokens = count_tokens(response_content)

        # Process response
        result = extract_location_json(response)

    except Exception as e:
        logger.error("API call failed: %s", e)
        result = LocationAdviceResponse(
            response="I couldn't process your request properly.",
            error=str(e)
        )
        output_tokens = 0

    # Save interaction
    token_counts = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens
    }

    request_data = {
        "request_type": "location_advice",
        "timestamp": int(time.time()),
        "prompt": prompt,
        "context": user_history,
        "system_content": api_request["messages"][0]["content"],
        "api_request": api_request,
        "api_response": response_data,
        "token_counts": token_counts
    }

    # In get_location_advice.py, fix the history recording:
    history_manager.add_llm_interaction(
        conversation_id=conversation_id,
        response=result,
        request_data=request_data,
        top_candidates=top_candidates
    )
    save_request_data(
        conversation_id,
        "location_advice",
        prompt,
        user_history,
        api_request["messages"][0]["content"],
        response_data,
        token_counts
    )
    return LocationAdviceResponse(
        continuation=result.get("continuation"),
        response=result.get("response")
    )
