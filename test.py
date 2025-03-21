from src.history_manager import HistoryManager
from src.llamarequest import llm_api
from src.poi_filter import get_poi_data
from src.get_top_candidates import find_top_candidates
from src.get_location_advice import get_location_advice
import os


def get_llm_response(user_prompt, user_context):
    llm_response = llm_api(user_prompt, user_context)
    print("DEBUG: LLM Response:", llm_response)

    # Check if clarification is needed
    clarification_needed = llm_response.get("clarification", None)

    if clarification_needed:
        # Clarification is a string, we can check if it's asking for clarification
        if isinstance(clarification_needed, str):
            print("Clarification Needed:", clarification_needed)
            additional_input = input("Provide clarification: ")
            user_prompt += " " + additional_input
            llm_response = llm_api(user_prompt, user_context)
        else:
            clarification_question = clarification_needed.get("question", "")
            if clarification_question:
                print("Clarification Needed:", clarification_question)
                additional_input = input("Provide clarification: ")
                user_prompt += " " + additional_input
                llm_response = llm_api(user_prompt, user_context)

    if 'error' in llm_response:
        print("Error:", llm_response['error'])
        return None

    return llm_response


def poi_process(llm_response, latitude, longitude, search_radius):
    search_categories = llm_response.get("categories", [])
    if not search_categories:
        print("Failed to extract valid categories from LLM response.")
        return []

    candidates = get_poi_data(
        latitude, longitude, search_radius, search_categories)
    if not candidates:
        print("No POIs found based on your criteria.")
    return candidates


def candidates_process(candidates, latitude, longitude, search_radius, num_candidates):
    candidate_results = find_top_candidates(
        candidates, latitude, longitude, search_radius, num_candidates)
    return {"default": candidate_results} if not isinstance(candidate_results, dict) else candidate_results


def get_location_advice_for_prompt(top_candidates, user_prompt, previous_messages, latitude, longitude, search_radius):
    try:
        location_advice = get_location_advice(
            user_prompt, previous_messages, top_candidates, latitude, longitude, search_radius)
        return location_advice
    except Exception as e:
        print(f"Error during location advice processing: {e}")
        return {}


def main():
    # Initialize the history manager
    history_manager = HistoryManager()

    # Get or create conversation ID
    conversation_id_input = input(
        "Enter conversation ID (leave blank for new conversation): ")

    if conversation_id_input.strip():
        conversation_id = conversation_id_input
        # Check if conversation exists
        if not os.path.exists(history_manager.get_history_file_path(conversation_id)):
            print(f"Creating new conversation with ID: {conversation_id}")
            history_manager.create_conversation(conversation_id)
    else:
        conversation_id = history_manager.create_conversation()
        print(f"Created new conversation with ID: {conversation_id}")

    # Display conversation history
    messages = history_manager.get_messages(conversation_id)
    if messages:
        print("\n--- Conversation History ---")
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                print(f"User: {content}")
            elif role == "assistant":
                print(f"Bot: {content}")
        print("--- End of History ---\n")
    else:
        print("No previous messages in this conversation.")

    # Set default location parameters
    latitude = 41.064108
    longitude = 29.031473
    search_radius = 2000
    num_candidates = 2

    while True:
        # Get the most recent top candidates from history
        top_candidates = history_manager.get_top_candidates(conversation_id)

        # Get user input
        user_prompt = input("\nEnter your prompt (or type 'exit' to quit): ")
        if user_prompt.lower() == 'exit':
            break

        # Get formatted history for context
        formatted_history = history_manager.get_formatted_history(
            conversation_id)

        # If we don't have top candidates yet, we need to get them
        if not top_candidates:
            # Call LLM API to get categories
            llm_response = llm_api(
                prompt=user_prompt,
                user_context=formatted_history,
                conversation_id=conversation_id,
                history_manager=history_manager
            )

            if llm_response is None or 'error' in llm_response:
                print("Error in LLM processing. Please try again.")
                continue

            # Handle clarification if needed
            clarification_needed = llm_response.get("clarification", None)
            if clarification_needed:
                print("Clarification Needed:", clarification_needed)
                additional_input = input("Provide clarification: ")
                user_prompt += " " + additional_input

                # Add clarification to history
                history_manager.add_user_message(
                    conversation_id, additional_input, {"clarification": True})

                # Get updated response
                llm_response = llm_api(
                    prompt=user_prompt,
                    user_context=formatted_history,
                    conversation_id=conversation_id,
                    history_manager=history_manager
                )

            # Get POI data
            candidates = get_poi_data(
                latitude, longitude, search_radius, llm_response.get(
                    "categories", [])
            )

            if not candidates:
                print("No POIs found based on your criteria.")
                continue

            # Process candidates
            top_candidates = find_top_candidates(
                candidates, latitude, longitude, search_radius, num_candidates
            )

            # Format for dictionary if needed
            if not isinstance(top_candidates, dict):
                top_candidates = {"default": top_candidates}

        # Get location advice based on top candidates
        location_advice = get_location_advice(
            prompt=user_prompt,
            history=formatted_history,
            top_candidates=top_candidates,
            latitude=latitude,
            longitude=longitude,
            search_radius=search_radius,
            conversation_id=conversation_id,
            history_manager=history_manager
        )

        # Print the response
        response_text = location_advice.get(
            "response", "No response received.")
        print("\nLocation Advice:", response_text)

        # We don't need to save history here as it's done in the API functions


if __name__ == "__main__":
    main()
