import re
import json
import numpy as np
import os
import uuid
import time
from config import LLAMA_API
from src.utils import timing_decorator
from src.history_manager import HistoryManager


def count_tokens(text):
    """
    Approximate token counter - actual implementation would depend on the tokenizer
    This is a simple approximation based on whitespace and punctuation
    """
    # Split by whitespace
    tokens = text.split()
    # Account for punctuation
    token_count = len(tokens)
    # Add estimated tokens for punctuation and special characters
    punctuation_count = sum(1 for char in text if char in '.,;:!?()[]{}"\'')
    return token_count + punctuation_count


@timing_decorator
def extract_json(response):
    response_data = response.json()
    print("response:", response_data)

    content = response_data['choices'][0]['message']['content']

    try:
        result = json.loads(content)
        print("✅ Direct JSON parsing successful.")
        return result
    except json.JSONDecodeError:
        print("❌ Direct JSON parsing failed. Trying regex extraction...")

    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        json_str = match.group(0).strip()
        try:
            result = json.loads(json_str)
            print("✅ Regex JSON extraction successful.")
            return result
        except json.JSONDecodeError:
            print("❌ Regex JSON extraction also failed.")

    print("❌ No valid JSON found.")
    return None


def save_request_data(conversation_id, request_type, prompt, context, system_content, response, token_counts, top_candidates=None):
    """
    Save request data to a JSON file
    """
    # Create a directory for requests if it doesn't exist
    os.makedirs("requests", exist_ok=True)

    # Create a unique filename
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
        print(f"Request saved to {filename}")
    except Exception as e:
        print(f"Error saving request data: {e}")


@timing_decorator
def format_top_candidates(top_candidates):
    lines = []

    # Expecting top_candidates as a dictionary with keys like "drive", "walk", etc.
    for mode, candidates in top_candidates.items():
        lines.append(f"{mode.capitalize()} Mode:")

        if candidates and len(candidates) > 0:
            for poi in candidates:
                details = [f"Mode: {mode.capitalize()}"]

                # Iterate over all fields in the POI and append them if they have valid values
                for key, value in poi.items():
                    # Exclude None or NaN values (handling both native floats and numpy floats)
                    if value is None or (isinstance(value, (float, np.floating)) and np.isnan(value)):
                        continue

                    # Handle nested dictionaries if any (for example, coordinates)
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

    # If no lines were added, add a default message
    if len(lines) == 0:
        lines.append("No location data available.")

    return "\n\n".join(lines)


@timing_decorator
def get_location_advice(prompt, history, top_candidates, latitude, longitude, search_radius, conversation_id=None, history_manager=None):
    # Generate a temporary conversation ID if none provided
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())

    # Create a history manager if not provided
    if history_manager is None:
        history_manager = HistoryManager()

    # Ensure that top_candidates is in dictionary format.
    # Make a deep copy to avoid modifying the original data
    if isinstance(top_candidates, list):
        formatted_candidates = {"default": top_candidates}
    else:
        # Create a new dictionary to avoid reference issues
        formatted_candidates = {}
        for mode, candidates in top_candidates.items():
            formatted_candidates[mode] = candidates.copy() if candidates else [
            ]

    # Now format the candidates and keep the formatted text
    context_text = format_top_candidates(formatted_candidates)

    # Get formatted history from the history manager
    if isinstance(history, list):
        user_history = "\n".join(history) if history else "None"
    else:
        # If history is not a list, try to get it from the history manager
        user_history = "\n".join(
            history_manager.get_formatted_history(conversation_id))

    # System content for token counting
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

    api_request_json = {
        "model": "llama3.1-70b",
        "messages": [
            {
                "role": "system",
                "content": system_content
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "functions": [
            {
                "name": "analyze_location_request",
                "description": (
                    "Determines if the prompt is a continuation of the conversation or a new request. "
                    "If it's a continuation, return continuation: true. "
                    "If it's not, return continuation: false and generate a response based on context and history to answer the users questions using all provided context."
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
                            "description": "A response to answer the users prompt or continue the conversation. A detailed response using context given above that would answer the users prompt. share address and coordinates if possible. and also more details on how they can get there"
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

    # Count tokens in request
    input_tokens = count_tokens(system_content) + count_tokens(prompt)

    # Make API request
    response = LLAMA_API.run(api_request_json)

    # Extract response content
    response_data = response.json()
    print("\n\nDebug: response_data:", response_data)
    print("\n\n")

    response_content = response_data['choices'][0]['message']['content']

    # Count tokens in response
    output_tokens = count_tokens(response_content)

    # Calculate total tokens
    total_tokens = input_tokens + output_tokens

    # Token counts dictionary
    token_counts = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens
    }

    parsed_json = extract_json(response)

    result = {}
    if parsed_json:
        result = {
            "continuation": parsed_json.get("continuation", False),
            "response": parsed_json.get("response", "I couldn't process your request properly.")
        }
    else:
        result = {"error": "Failed to process response",
                  "raw_response": response_content}

    # Create a full request data dictionary for history
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

    # Save to history
    history_manager.add_llm_interaction(
        conversation_id=conversation_id,
        prompt=prompt,
        response=result,
        request_data=request_data,
        top_candidates=top_candidates
    )

    return result
