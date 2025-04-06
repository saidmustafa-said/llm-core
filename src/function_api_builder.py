def create_classification_request(
    prompt,
    user_context,
    existing_subcategories,
    existing_tags
):
    """Builds the API request payload for location classification without function calling."""

    system_content = (
        "You are a Location Classification AI. Your task is to analyze user input and determine relevant subcategories and descriptive tags.\n\n"

        "CURRENT CONTEXT:\n"
        f"Existing subcategories: {existing_subcategories}\n"
        f"Existing descriptive tags: {existing_tags}\n"
        f"User conversation history:\n{user_context}\n\n"

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
            {"role": "user", "content": f"Classify this request: '{prompt}'"}
        ],
        "max_tokens": 5000,
        "temperature": 0.2,
        # Ensures structured JSON output
        "response_format": {"type": "json_object"}
    }

    return api_request


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
        "   - IMPORTANT: If asking for more details about places mentioned in context, DO NOT trigger new searches\n"
        "   - Respond with location details using Δ{{\"response\": \"...\", \"continuation\": bool}}Δ\n"
        "   - Include all available information like address, hours, distance, and key amenities\n\n"

        "2. If needing new data search (ONLY when user asks for entirely new location types/radius/places NOT in current context):\n"
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
        "Context answer (when asking about existing places): Δ{{\n"
        "  \"response\": \"Nilly cafe is located at Arnavutköy Kuruçeşme Caddesi. Based on available information, it's 932m away on foot. The cafe is known for its [any details from context]. Would you like directions or information about another place?\",\n"
        "  \"continuation\": true\n}}Δ\n\n"

        "Action required (ONLY for new searches): Δ{{\n"
        "  \"action\": \"classification_agent\",\n"
        "  \"prompt\": \"Find pet-friendly cafes with outdoor seating within 500m of X location\",\n"
        "  \"longitude\": 00.000000,\n"
        "  \"latitude\": 00.000000,\n"
        "  \"radius\": 500\n}}Δ\n\n"

        "STRICT RULES:\n"
        "- ALWAYS wrap JSON in Δ delimiters\n"
        "- Use either 'response' or 'action' never both\n"
        "- Include exact coordinates from context when referencing specific places\n"
        "- If asking for more details about places ALREADY in context, use 'response' format with existing data\n"
        "- ONLY trigger classification_agent for ENTIRELY NEW location queries not covered in context\n"
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
