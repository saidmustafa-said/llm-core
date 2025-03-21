import re
import json
import numpy as np
import os
import uuid
import time
import logging
from config import LLAMA_API
from src.utils import timing_decorator, count_tokens, extract_json_from_text
from src.history_manager import HistoryManager
from src.data_types import TopCandidates, POIData
from typing import List,


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


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
            json.dump(data, f, indent=2)
        logger.info("Request saved to %s", filename)
    except Exception as e:
        logger.error("Error saving request data: %s", e)


@timing_decorator
def format_top_candidates(top_candidates):
    """
    Format top candidate points of interest into a readable string.
    Expects top_candidates as a dictionary (e.g. with keys like "drive", "walk").
    """
    lines = []
    for mode, candidates in top_candidates.items():
        lines.append(f"{mode.capitalize()} Mode:")
        if candidates and len(candidates) > 0:
            for poi in candidates:
                details = [f"Mode: {mode.capitalize()}"]
                for key, value in poi.items():
                    if value is None or (isinstance(value, (float, np.floating)) and np.isnan(value)):
                        continue
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if sub_value is None or (isinstance(sub_value, (float, np.floating)) and np.isnan(sub_value)):
                                continue
                            details.append(
                                f"{sub_key.capitalize()}: {sub_value}")
                    else:
                        details.append(f"{key.capitalize()}: {value}")
                lines.append("\n".join(details))
        else:
            lines.append(
                f"No locations found within the specified route distance for {mode} mode.")
    if not lines:
        lines.append("No location data available.")
    return "\n\n".join(lines)


@timing_decorator
def get_location_advice(prompt: str, history: List[str],
                        top_candidates: TopCandidates,
                        latitude: float, longitude: float,
                        search_radius: int,
                        conversation_id: Optional[str] = None,
                        history_manager: Optional[HistoryManager] = None) -> Dict:
    """
    Generate location advice based on the prompt, previous conversation history, 
    and top candidate locations. Also saves the full interaction in history.
    """
    # Generate a temporary conversation ID if none is provided.
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())

    # Use the provided history manager or create a new one.
    if history_manager is None:
        history_manager = HistoryManager()

    # Ensure top_candidates is a dictionary.
    if isinstance(top_candidates, list):
        formatted_candidates = {"default": top_candidates}
    else:
        formatted_candidates = {mode: candidates.copy(
        ) if candidates else [] for mode, candidates in top_candidates.items()}

    context_text = format_top_candidates(formatted_candidates)

    # Determine user conversation history.
    if isinstance(history, list):
        user_history = "\n".join(history) if history else "None"
    else:
        user_history = "\n".join(
            history_manager.get_formatted_history(conversation_id))

    # Build the system content that will guide the LLAMA_API.
    system_content = (
        "You are a friendly and helpful assistant who specializes in location recommendations. "
        "Think of yourself as a knowledgeable local friend who's helping someone navigate the area. "
        "Make recommendations based on the provided context data about nearby locations.\n\n"
        "**User Information:**\n"
        f"- Latitude: {latitude}\n"
        f"- Longitude: {longitude}\n"
        f"- Search Radius: {search_radius}\n\n"
        "**Guidelines:**\n"
        "- Be conversational and casual, like you're texting a friend.\n"
        "- If the context contains location data, provide specific recommendations.\n"
        "- If the context is empty or limited, acknowledge this but still be helpful by:\n"
        "  • Asking for more details about what they're looking for.\n"
        "  • Suggesting they increase their search radius.\n"
        "  • Offering general advice based on what you do know.\n"
        "- For each recommendation, include key details when available: name, address, distance, and coordinates.\n"
        "- Keep responses concise but informative.\n"
        "- Consider transportation modes (walking, driving) in your suggestions.\n"
        "- Match your tone to the user's query - be upbeat for entertainment queries, practical for necessities.\n\n"
        "**User Conversation History:**\n"
        f"{user_history}\n\n"
        "**Context Information:**\n\n"
        f"{context_text}\n"
    )

    # Prepare the API request payload.
    api_request_json = {
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

    # Token counting for cost estimation.
    input_tokens = count_tokens(system_content) + count_tokens(prompt)
    response = LLAMA_API.run(api_request_json)
    response_data = response.json()
    logger.debug("Response Data: %s", response_data)

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

    # Extract JSON from the response using the common utility.
    parsed_json = extract_json_from_text(response)
    if parsed_json:
        result = {
            "continuation": parsed_json.get("continuation", False),
            "response": parsed_json.get("response", "I couldn't process your request properly.")
        }
    else:
        result = {
            "error": "Failed to process response",
            "raw_response": response_content
        }

    # Prepare data to save the complete interaction to history.
    request_data = {
        "request_type": "location_advice",
        "timestamp": int(time.time()),
        "prompt": prompt,
        "context": user_history,
        "system_content": system_content,
        "api_request": api_request_json,
        "api_response": response_data,
        "token_counts": token_counts
    }

    history_manager.add_llm_interaction(
        conversation_id=conversation_id,
        prompt=prompt,
        response=result,
        request_data=request_data,
        top_candidates=top_candidates
    )

    save_request_data(conversation_id, "location_advice", prompt, user_history,
                      system_content, response_data, token_counts, top_candidates)
    return result


