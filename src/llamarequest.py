from utils import timing_decorator
from llamaapi import LlamaAPI
from dotenv import load_dotenv
import os
import pandas as pd
import json
import re


# Initialize the LlamaAPI SDK
load_dotenv()
api_key = os.getenv("apiKey")

llama = LlamaAPI(api_key)


@timing_decorator
def retrieve_tags():
    """
    Retrieves tags from the CSV file (tags.csv) and returns them as a formatted string.
    """
    tags_file = os.path.join("great_data", "tags.csv")

    if not os.path.exists(tags_file):
        return "None"

    tags_df = pd.read_csv(tags_file)

    if 'tags' in tags_df.columns:
        tags_list = tags_df['tags'].dropna().tolist()
        return ", ".join(tags_list) if tags_list else "None"
    else:
        return "None"


@timing_decorator
def extract_json(response):
    response_data = response.json()
    print("response:", response_data)

    content = response_data['choices'][0]['message']['content']

    # Try direct JSON parsing first
    try:
        result = json.loads(content)
        print("✅ Direct JSON parsing successful.")
        return result
    except json.JSONDecodeError:
        print("❌ Direct JSON parsing failed. Trying regex extraction...")

    # Try regex extraction if direct parsing fails
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        json_str = match.group(0).strip()  # Extract JSON portion
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
    existing_tags_str = retrieve_tags()

    api_request_json = {
        "model": "llama3.1-70b",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an AI specialized in location tagging. "
                    f"Here are the existing tags: {existing_tags_str}. "
                    "Your task is to analyze the user's prompt and see if any of the existing tags match. "
                    "If they don't fully capture the essence of the prompt, generate new tags that better fit the user's request. "
                    "Return the result strictly in JSON format with two arrays: 'existed_tags' for matched tags and 'new_tag' for newly generated ones."
                )
            },
            {
                "role": "user",
                "content": f"Analyze this prompt and extract tags: '{prompt}'"
            }
        ],
        "functions": [
            {
                "name": "extract_location_tags",
                "description": (
                    "Extract the most relevant tags based on the user's prompt. "
                    "First, compare the prompt with the existing tags. If any existing tag (or its synonym) matches the prompt, return that tag. "
                    "If no perfect match exists, generate new tags that are unique and non-redundant. "
                    "Do not create synonyms or variations of existing tags when generating new tags."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "existed_tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of tags that match the existing tags"
                        },
                        "new_tag": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of new tags generated from the prompt"
                        }
                    },
                    "required": ["existed_tags", "new_tag"]
                }
            }
        ],
        "function_call": "extract_location_tags",
        "max_tokens": 200,
        "temperature": 0.2,
        "top_p": 0.9,
        "frequency_penalty": 0.8,
        "presence_penalty": 0.3,
        "stream": False
    }

    response = llama.run(api_request_json)
    parsed_json = extract_json(response)

    if parsed_json:
        print("🎯 Final extracted JSON:", parsed_json)
        return parsed_json
    else:
        print("🚨 Failed to extract JSON.")
        return None  # Explicitly return None if extraction fails
