from src.data_types import LLMResponse, TopCandidates
from src.get_location_advice import get_location_advice
from src.get_top_candidates import find_top_candidates
from src.poi_filter import get_poi_data
from src.llamarequest import llm_api
from src.history_manager import HistoryManager
import os
from src.logger_setup import logger_instance


def handle_clarification(llm_response: LLMResponse, prompt: str, formatted_history: str, conversation_id: str, user_id: str, history_manager: HistoryManager) -> str:
    clarification = llm_response.get("clarification")
    if clarification:
        if isinstance(clarification, str):
            question = clarification
        else:
            question = clarification.get('question', '')

        additional_input = input(
            f"Clarification Needed: {question}\nProvide clarification: ")

        # Save the user's clarification to history
        history_manager.add_user_message(
            user_id, conversation_id, additional_input)

        # Fetch updated history including the new message
        updated_history = history_manager.get_formatted_history(
            user_id, conversation_id)

        # Re-run the llm_api with the new input and updated history
        llm_response = llm_api(additional_input, updated_history)

        # Check for further clarification recursively
        if llm_response.get("clarification"):
            return handle_clarification(llm_response, additional_input, updated_history, conversation_id, user_id, history_manager)

    return prompt


def process_new_query(user_prompt: str, formatted_history: str, conversation_id: str,
                      user_id: str, history_manager: HistoryManager, latitude: float, longitude: float,
                      search_radius: int, num_candidates: int) -> TopCandidates:
    """Process a new user query to get new top candidates."""
    # Save the user message to history before processing
    history_manager.add_user_message(user_id, conversation_id, user_prompt)

    # Get initial LLM classification response
    llm_response = llm_api(user_prompt, formatted_history)
    print(llm_response)
    print(llm_response.get("categories", []))

    if llm_response is None or 'error' in llm_response:
        print("Error in LLM processing. Please try again.")
        return None

    # Handle any clarification request from the LLM
    user_prompt = handle_clarification(
        llm_response, user_prompt, formatted_history, conversation_id, user_id, history_manager)
    if not user_prompt:
        return None  # If there's an error, return None

    categories = llm_response.get("categories", [])
    print(f"Categories to search for: {categories}")

    candidates = get_poi_data(latitude, longitude, search_radius, categories)
    if not candidates:
        print("No POIs found based on your criteria.")
        return None

    top_candidates = find_top_candidates(
        candidates, latitude, longitude, search_radius, num_candidates)
    if not isinstance(top_candidates, dict):
        top_candidates = {"default": top_candidates}

    return top_candidates


def main():
    user_id = "test_user"  # Default user id for history tracking
    logger_instance.initialize_logging_context(user_id, 'api_execution')
    logger = logger_instance.get_logger()
    logger.info("Logging setup completed")

    history_manager = HistoryManager()

    conversation_id_input = input(
        "Enter conversation ID (leave blank for new conversation): ")
    if conversation_id_input.strip():
        conversation_id = conversation_id_input.strip()
        # If no history file exists, create a new conversation for the user.
        if not os.path.exists(history_manager.get_conversation_file_path(user_id, conversation_id)):
            print(f"Creating new conversation with ID: {conversation_id}")
            history_manager.create_conversation(user_id, conversation_id)
    else:
        conversation_id = history_manager.create_conversation(user_id)
        print(f"Created new conversation with ID: {conversation_id}")

    messages = history_manager.get_messages(user_id, conversation_id)
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

    # Default location parameters
    latitude = 41.064108
    longitude = 29.031473
    search_radius = 2000
    num_candidates = 2

    top_candidates = None
    reuse_prompt = False
    last_prompt = ""

    while True:
        if not reuse_prompt:
            user_prompt = input(
                "\nEnter your prompt (or type 'exit' to quit): ")
            if user_prompt.lower() == 'exit':
                break
            last_prompt = user_prompt
        else:
            user_prompt = last_prompt
            reuse_prompt = False
            print(f"\nReusing last prompt: {user_prompt}")

        formatted_history = history_manager.get_formatted_history(
            user_id, conversation_id)

        # If we don't have top candidates yet, process a new query
        if not top_candidates:
            top_candidates = process_new_query(user_prompt, formatted_history, conversation_id,
                                               user_id, history_manager, latitude, longitude, search_radius, num_candidates)
            if not top_candidates:
                continue  # Skip to next loop iteration if processing failed

        # Get location advice based on the top candidates
        try:
            location_advice = get_location_advice(user_prompt, formatted_history, top_candidates,
                                                  latitude, longitude, search_radius)
        except Exception as e:
            print(f"Error during location advice processing: {e}")
            continue

        response_text = location_advice.get(
            "response", "No response received.")
        # Save the assistant's response to history
        history_manager.add_assistant_message(
            user_id, conversation_id, response_text)
        print("\nLocation Advice:", response_text)

        # Ask for follow-up input regardless of the continuation value
        user_prompt = input(
            "\nEnter follow-up question (or type 'new' to start new search): ")
        if user_prompt.lower() == 'exit':
            break

        # Save follow-up question and refresh history
        history_manager.add_user_message(user_id, conversation_id, user_prompt)
        formatted_history = history_manager.get_formatted_history(
            user_id, conversation_id)

        # Get second location advice with the follow-up question
        try:
            location_advice = get_location_advice(user_prompt, formatted_history, top_candidates,
                                                  latitude, longitude, search_radius)
        except Exception as e:
            print(f"Error during location advice processing: {e}")
            continue

        continuation = str(location_advice.get(
            "continuation", "false")).lower()
        response_text = location_advice.get(
            "response", "No response received.")
        history_manager.add_assistant_message(
            user_id, conversation_id, response_text)
        print("\nLocation Advice:", response_text)

        if continuation == "false":
            break

        # Now check if we should enter the continuation loop
        while continuation == "true":
            user_prompt = input(
                "\nEnter your prompt (or type 'exit' to quit): ")
            if user_prompt.lower() == 'exit':
                break
            last_prompt = user_prompt  # Update the last prompt

            # Save the new prompt and refresh history
            history_manager.add_user_message(
                user_id, conversation_id, user_prompt)
            formatted_history = history_manager.get_formatted_history(
                user_id, conversation_id)

            try:
                location_advice = get_location_advice(user_prompt, formatted_history, top_candidates,
                                                      latitude, longitude, search_radius)
            except Exception as e:
                print(f"Error during location advice processing: {e}")
                continue

            continuation = str(location_advice.get(
                "continuation", "false")).lower()
            response_text = location_advice.get(
                "response", "No response received.")
            history_manager.add_assistant_message(
                user_id, conversation_id, response_text)
            print("\nLocation Advice:", response_text)

            if continuation == "false":
                break

        if continuation == "false":
            # If continuation is false, clear top_candidates to get new ones on next iteration
            print("Starting new recommendation context with the same prompt.")
            top_candidates = None
            reuse_prompt = True  # Flag to reuse the last prompt


if __name__ == "__main__":
    main()
