
import os
import json
from config import LLAMA_API


def build_location_request(prompt, context_text, user_history, latitude, longitude, search_radius):
    """Builds the API request payload for location recommendations without function calling."""

    system_content = (
        "You are a Location Intelligence Assistant. You have two response modes:\n\n"
        "CURRENT CONTEXT:\n"
        f"User coordinates: ({latitude}, {longitude})\n"
        f"Search radius: {search_radius}m\n"
        f"Available locations:\n{context_text}\n\n"
        f"Conversation history:\n{user_history}\n\n"

        "RESPONSE RULES:\n"
        "1. If query can be answered with current context:\n"
        "   - Respond with location details using Δ{{\"response\": \"...\"}}Δ\n"
        "   - Include address, hours, distance, and key amenities\n\n"

        "2. If needing new data search (user asks for different location type/radius/near specific place):\n"
        "   - Use classification_agent action format:\n"
        "     Δ{{\n"
        "       \"action\": \"classification_agent\",\n"
        "       \"prompt\": \"Detailed search description including place types and requirements\",\n"
        "       \"longitude\": ...,\n"
        "       \"latitude\": ...,\n"
        "       \"radius\": ...\n"
        "     }}Δ\n\n"

        "COORDINATE HANDLING:\n"
        "- For 'near [previous place]' queries: Use that place's coordinates from context\n"
        "- Default to user's current coordinates otherwise\n\n"

        "EXAMPLE RESPONSES:\n"
        "Context answer: Δ{{\n"
        "  \"response\": \"The closest parking to X location is at XYZ Garage (3min walk). Open 24/7, €5/h.\"}}Δ\n\n"

        "Action required: Δ{{\n"
        "  \"action\": \"classification_agent\",\n"
        "  \"prompt\": \"Find pet-friendly cafes with outdoor seating within 500m of X location\",\n"
        "  \"longitude\": 00.000000,\n"
        "  \"latitude\": 00.000000,\n"
        "  \"radius\": 500\n}}Δ\n\n"

        "STRICT RULES:\n"
        "- ALWAYS wrap JSON in Δ delimiters\n"
        "- Use either 'response' or 'action' never both\n"
        "- Include exact coordinates from context when referencing specific places\n"
        "- If context lacks required info, trigger classification_agent\n"
        "- Maintain natural conversation flow in responses"
    )

    api_request = {
        "model": "llama3.1-70b",
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 7000,
        "temperature": 0.2,
        "response_format": {"type": "json_object"}  # Encourages JSON output
    }

    return api_request


def extract_json():
    """
    Reads and returns the JSON content of 'tempshold.json' as a JSON string.
    """
    filename = "tempshold.json"

    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
                return json.dumps(data, indent=4)
            except json.JSONDecodeError:
                return "{}"
    return "{}"


json_output = extract_json()  # This is a JSON string
parsed_output = json.loads(json_output)  # Convert it to a dictionary


prompt = "is there a parking close to it"
context_text = parsed_output['context_text']
user_history = parsed_output['user_history']
latitude = parsed_output['latitude']
longitude = parsed_output['longitude']
search_radius = parsed_output['search_radius']


api_request = build_location_request(
    prompt, context_text, user_history, latitude, longitude, search_radius)

# print(api_request)
response = LLAMA_API.run(api_request)

print(response.json())


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


extracted_json = extract_content(response.json())
print(extracted_json)

if not extracted_json:
    print("No valid content extracted.")

if "response" in extracted_json:
    print("Handling direct response:", extracted_json["response"])
    # Handle response type (e.g., displaying location details)
elif "action" in extracted_json and extracted_json["action"] == "classification_agent":
    print("Triggering new search with criteria:", extracted_json["action"])
    # Handle classification agent type (e.g., calling an API for new data search)
else:
    print("Unknown response format.")
