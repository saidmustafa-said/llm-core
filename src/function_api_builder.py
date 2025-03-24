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
                                    "description": "True if clarification is needed, False if the classification is certain. None if conversation has ended"
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


def build_location_request(prompt, context_text, user_history, latitude, longitude, search_radius):
    """Builds the API request payload for location recommendations."""
    system_content = (
        "You are a friendly location recommendation assistant. "
        f"User coordinates: ({latitude}, {longitude}), Search radius: {search_radius}m\n"
        "In users radius these are the only ones found, if asked if there is more, say these are the only ones in the radius user have chosen in that longitude and latitude"
        f"Context data:\n{context_text}\n\n"
        f"Conversation history:\n{user_history}\n\n"
        "Engage in a conversational manner, answering questions based on history and context. "
        "Keep the conversation natural and fluid, providing recommendations with details like addresses, directions, opening hours, or amenities when available. "
        "Ensure that responses always contain useful information, even if context is limited."
    )

    api_request = {
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
                    "If it's a continuation, return continuation: true. Otherwise, return continuation: false and "
                    "generate a conversational response that answers the user's question based on history and context. "
                    "Always provide a response even during continuations. "
                    "If descriptions are missing, use default responses to ensure the conversation continues smoothly. "
                    "Make sure the response is full, even if not all details are available. Always provide details like address, hours, and amenities when possible."
                    "Answer only based on the context data, if not in context data then set continuation to false"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "response": {
                            "type": "string",
                            "description": (
                                "A natural and engaging response that keeps the conversation going, answering the user's question using context and history. "
                                "MUST always provide a response, even if context is limited. The response should be informative, with as much detail as possible, "
                                "including address, hours, amenities, or directions if available."
                                "Always answer the users prompt in full"
                                "Answer only based on the context data, if not in context data then set continuation to false"
                            )
                        },
                        "continuation": {
                            "type": "boolean",
                            "description": (
                                "True if the query is a continuation, False if it's a new request."
                            )
                        }
                    },
                    "required": ["continuation", "response"]
                }
            }
        ],
        "function_call": "analyze_location_request",
        "max_tokens": 7000,
        "temperature": 0.2,
    }

    return api_request
