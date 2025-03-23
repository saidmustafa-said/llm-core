def create_classification_request(
    prompt,
    user_context,
    existing_subcategories,
    existing_tags,
    system_overview
):
    """
    Builds the API request payload for location classification.
    """

    system_content = (
        "You are an AI specializing in location classification. "
        f"Existing subcategories: {existing_subcategories}. "
        f"Existing descriptive tags: {existing_tags}. "
        f"User conversation history: {user_context}. "
        f"{system_overview} "
        "Analyze the user's prompt to determine which subcategories (only subcategory names, not categories) "
        "it fits into and which descriptive tags apply. "
        "Return the matching subcategories and descriptive tags. "
        "If the prompt does not exactly match any existing tag, generate new ones that better capture its essence. "
        "Return both subcategories and descriptive tags. "
        "If multiple valid subcategories exist and the intent is unclear, return a clarification question."
    )

    api_request = {
        "model": "llama3.1-70b",
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": f"Analyze this prompt: '{prompt}'"}
        ],
        "functions": [
            {
                "name": "extract_location_info",
                "description": (
                    "Extract the most relevant subcategories and descriptive tags from the user's prompt based on the provided context. "
                    "For subcategories, compare the prompt with the existing list and return the relevant matches. "
                    "For descriptive tags, do the same by returning matched tags or generating new descriptive words that capture the location's nuances. "
                    "Ensure both subcategories and tags are unique, non-redundant, and appropriately capture the nuances of the location described in the prompt. "
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

    return api_request
