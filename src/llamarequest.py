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
def llm_api(prompt):
    """
    Interacts with the Llama API to send a prompt and retrieve tags based on the user's input.
    """
    existing_tags_str, existing_subcategories_str = retrieve_tags()

    api_request_json = {
        "model": "llama3.1-70b",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an AI specialized in location classification. "
                    f"Existing subcategories (only subcategory values): {existing_subcategories_str}. "
                    f"Existing descriptive tags: {existing_tags_str}. "
                    "Analyze the user's prompt to determine which subcategories (only subcategory names, not categories) it fits into and which descriptive tags apply. "
                    "Return the matching subcategories and descriptive tags. "
                    "If the prompt does not exactly match any existing tag, generate new ones that better capture its essence. "
                    "Return both subcategories and descriptive tags."
                )
            },
            {
                "role": "user",
                "content": f"Analyze this prompt and extract subcategories and tags: '{prompt}'"
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
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subcategories": {
                            "type": "object",
                            "properties": {
                                "findings": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List the subcategories that match the prompt. List top 3 only subcategory names."
                                }
                            },
                            "required": ["findings"]
                        },
                        "tags": {
                            "type": "object",
                            "properties": {
                                "existed": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List top 3 descriptive tags that match the existing ones and capture the location's nuances."
                                },
                                "new": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of new descriptive tags generated from the prompt that capture the location's nuances."
                                }
                            },
                            "required": ["existed", "new"]
                        }
                    },
                    "required": ["subcategories", "tags"]
                }
            }
        ],
        "function_call": "extract_location_info",
        "max_tokens": 500,
        "temperature": 0.2,
        "top_p": 0.9,
        "frequency_penalty": 0.8,
        "presence_penalty": 0.3,
        "stream": False
    }

    response = LLAMA_API.run(api_request_json)
    parsed_json = extract_json(response)

    if parsed_json:
        print("🎯 Final extracted JSON:", parsed_json)
        return parsed_json
    else:
        print("🚨 Failed to extract JSON.")
        return None
