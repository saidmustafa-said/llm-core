
import os
import json
from config import LLAMA_API


def create_classification_request(
    prompt,
    user_context,
    existing_subcategories,
    existing_tags,
    system_overview
):
    """Builds the API request payload for location classification without function calling."""

    system_content = (
        "You are a Location Classification AI. Your task is to analyze user input and determine relevant subcategories and descriptive tags.\n\n"

        "CURRENT CONTEXT:\n"
        f"Existing subcategories: {existing_subcategories}\n"
        f"Existing descriptive tags: {existing_tags}\n"
        f"User conversation history:\n{user_context}\n\n"
        f"{system_overview}\n\n"

        "CLASSIFICATION RULES:\n"
        "1. Match the user’s prompt to relevant subcategories (return only subcategory names, not general categories)\n"
        "2. Identify existing descriptive tags that fit, and create new ones if needed\n"
        "3. If the user intent is unclear, return a clarification question **instead** of classification\n\n"

        "RESPONSE FORMATS:\n"
        "If classification is clear:\n"
        "   Δ{{\n"
        "     \"subcategories\": [\"subcategory1\", \"subcategory2\"],\n"
        "     \"tags\": {\"existed\": [\"tag1\", \"tag2\"], \"new\": [\"new_tag1\"]}\n"
        "   }}Δ\n\n"

        "If clarification is needed:\n"
        "   Δ{{\n"
        "     \"clarification\": \"Do you mean X or Y?\"\n"
        "   }}Δ\n\n"

        "STRICT RULES:\n"
        "- ALWAYS wrap JSON responses in Δ delimiters\n"
        "- Provide either `subcategories` & `tags`, OR `clarification`—NEVER both\n"
        "- Responses must be concise and relevant, avoiding redundancy\n"
    )

    api_request = {
        "model": "llama3.1-70b",
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 5000,
        "temperature": 0.2,
        # Ensures structured JSON output
        "response_format": {"type": "json_object"}
    }

    return api_request


def extract_json():
    """
    Reads and returns the JSON content of 'tempshold.json' as a JSON string.
    """
    filename = "tempshold2.json"

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


prompt = "is there a close by cafe with a nice view"
user_context = parsed_output['user_context']
existing_subcategories = parsed_output['existing_subcategories']
existing_tags = parsed_output['existing_tags']
system_overview = parsed_output['system_overview']


api_request = create_classification_request(
    prompt,
    user_context,
    existing_subcategories,
    existing_tags,
    system_overview
)

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

if not extracted_json:
    print("No valid content extracted.")

if "clarification" in extracted_json:
    print("Handling direct response:", extracted_json["response"])
    # Handle response type (e.g., displaying location details)
elif "subcategories" in extracted_json and "tags" in extracted_json:
    print("Triggering new search with criteria:",
          extracted_json["subcategories"], extracted_json["tags"])
    # Handle classification agent type (e.g., calling an API for new data search)
else:
    print("Unknown response format.")
