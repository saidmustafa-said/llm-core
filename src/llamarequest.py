from src.utils import timing_decorator
import os
import pandas as pd
import json
import re
from config import TAGS_LIST, LLAMA_API, CATEGORY_SUBCATEGORY_LIST


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
            # Group by 'category' and aggregate the subcategories into a comma-separated string
            grouped = subcategory_df.groupby('category')['subcategory'].apply(
                lambda x: ",".join(x)).reset_index()

            # Format the string as Category: subcat,subcat,...
            subcategory_string = "\n".join(
                [f"{row['category']}: {row['subcategory']}" for _, row in grouped.iterrows()])
            subcategory_string = subcategory_string if subcategory_string else "None"

    return tags_string, subcategory_string


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
def llm_api(prompt, user_context=None):
    """
    LLM function that extracts subcategories and descriptive tags.
    If multiple subcategories are found, the LLM itself will ask for more detail.
    """
    existing_tags_str, existing_subcategories_str = retrieve_tags()
    user_history = "\n".join(user_context) if user_context else "None"

    api_request_json = {
        "model": "llama3.1-70b",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an AI specializing in location classification. "
                    f"Existing subcategories: {existing_subcategories_str}. "
                    f"Existing descriptive tags: {existing_tags_str}. "
                    f"User conversation history: {user_history}. "
                    "Analyze the user's prompt to determine which subcategories (only subcategory names, not categories) it fits into and which descriptive tags apply. "
                    "Return the matching subcategories and descriptive tags. "
                    "If the prompt does not exactly match any existing tag, generate new ones that better capture its essence. "
                    "Return both subcategories and descriptive tags."
                    "If multiple valid subcategories exist and the intent is unclear, return a clarification question."
                )
            },
            {
                "role": "user",
                "content": f"Analyze this prompt: '{prompt}'"
            }
        ],
        "functions": [
            {
                "name": "extract_location_info",
                "description": (
                    "Extract the most relevant subcategories and descriptive tags from the user's prompt based on the provided context. "
                    "For subcategories, compare the prompt with the existing list and return the relevant matches. "
                    "For descriptive tags, do the same by returning matched tags or generating new descriptive words that capture the location's nuances. "
                    "Ensure both subcategories and tags are unique, non-redundant, and appropriately capture the nuances of the location described in the prompt."
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

    response = LLAMA_API.run(api_request_json)
    parsed_json = extract_json(response)

    if parsed_json:
        # Get clarification if needed
        clarification_question = parsed_json['clarification'][
            'question'] if parsed_json['clarification']['needed'] else None

        # Categories and tags
        categories = parsed_json['subcategories']
        tags = parsed_json['tags']['existed']

        return {
            "clarification": clarification_question,
            "categories": categories,
            "tags": tags
        }

    return {"error": "Failed to extract JSON"}
