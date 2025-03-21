import json
import re
import numpy as np
from src.utils import timing_decorator
from config import LLAMA_API


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
def get_location_advice(prompt, history, top_candidates, latitude, longitude, search_radius):
    print("Debug: top_candidates before processing:", top_candidates)

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

    user_history = "\n".join(history) if history else "None"

    api_request_json = {
        "model": "llama3.1-70b",
        "messages": [
            {
                "role": "system",
                "content": (
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
            },
            {
                "role": "user",
                "content": f"Analyze this prompt: '{prompt}'"
            }
        ],
        "functions": [
            {
                "name": "analyze_location_request",
                "description": (
                    "Determines if the prompt is a continuation of the conversation or a new request. "
                    "If it's a continuation, return continuation: true. "
                    "If it's not, return continuation: false and generate a response based on all provided context."
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
                            "description": "A response to continue the conversation if continuation is true. A detailed response using context if continuation is false and the context is not empty."
                        }
                    },
                    "required": ["continuation", "response"]
                }
            }
        ],
        "function_call": "analyze_location_request",
        "max_tokens": 7000,
        "temperature": 0.7,
        "top_p": 0.95,
        "frequency_penalty": 0.5,
        "presence_penalty": 0.2,
        "stream": False
    }

    response = LLAMA_API.run(api_request_json)
    parsed_json = extract_json(response)

    if parsed_json:
        return {
            "continuation": parsed_json.get("continuation", False),
            "response": parsed_json.get("response", "I couldn't process your request properly.")
        }

    return {"error": "Failed to process response"}
