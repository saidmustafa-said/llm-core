from src.data_types import LLMResponse, TopCandidates
from src.get_location_advice import get_location_advice
from src.get_top_candidates import find_top_candidates
from src.poi_filter import get_poi_data
from src.llamarequest import llm_api
from src.history_manager import HistoryManager
import os
from src.logger_setup import logger_instance


def handle_clarification(llm_response: LLMResponse, prompt: str, formatted_history: str, conversation_id: str, user_id: str, history_manager: HistoryManager) -> tuple:
    """
    Handles any clarification needed from the LLM response in a while loop.
    Returns a tuple of (updated_prompt, updated_llm_response)
    """
    logger = logger_instance.get_logger()
    logger.info("Handling clarification")

    while True:
        clarification_value = llm_response.get("clarification")
        normalized_clarification = None
        if clarification_value is not None:
            if isinstance(clarification_value, dict) and "needed" in clarification_value:
                normalized_clarification = str(
                    clarification_value.get("needed")).strip().lower()
            else:
                normalized_clarification = str(
                    clarification_value).strip().lower()

        # Exit the loop if no clarification is needed (or clarification is 'false')
        if normalized_clarification is None or normalized_clarification == 'false':
            logger.info("No clarification needed - continuing process")
            break

        if normalized_clarification == 'true':
            logger.info(
                f"Clarification requested for conversation {conversation_id}")

            # Extract the clarification question
            question = ""
            if isinstance(clarification_value, str):
                question = clarification_value
            elif isinstance(clarification_value, dict):
                question = clarification_value.get('question', '')

            logger.debug(f"Clarification question: {question}")

            # Prompt for user input and wait for it
            additional_input = input(
                f"Clarification Needed: {question}\nProvide clarification: ")
            logger.info("User provided clarification input")

            # Save the user's clarification to history
            history_manager.add_user_message(
                user_id, conversation_id, additional_input)
            logger.debug("Clarification added to conversation history")

            # Fetch updated history including the new message
            formatted_history = history_manager.get_formatted_history(
                user_id, conversation_id)
            logger.debug("Retrieved updated conversation history")

            # Re-run the LLM API with the new input and updated history
            logger.info("Re-running LLM API with clarification")
            llm_response = llm_api(additional_input, formatted_history)
            logger.debug(f"Clarification response received: {llm_response}")

            # Update the prompt to reflect the new input
            prompt = additional_input
    logger.info("Clarification handling complete")
    return prompt, llm_response


def process_new_query(user_prompt: str, formatted_history: str, conversation_id: str,
                      user_id: str, history_manager: HistoryManager, latitude: float, longitude: float,
                      search_radius: int, num_candidates: int) -> TopCandidates:
    """Process a new user query to get new top candidates."""
    logger = logger_instance.get_logger()
    logger.info(f"Processing new query for conversation {conversation_id}")

    # Save the user message to history before processing
    history_manager.add_user_message(user_id, conversation_id, user_prompt)
    logger.debug("User message added to history")

    # Get initial LLM classification response
    logger.info("Initiating LLM API call")
    llm_response = llm_api(user_prompt, formatted_history)
    logger.debug(f"LLM response received: {llm_response}")

    if llm_response is None or 'error' in llm_response:
        logger.error("LLM processing error occurred")
        print("Error in LLM processing. Please try again.")
        return None

    # Handle any clarification request from the LLM iteratively
    logger.info("Checking for clarification needs")
    user_prompt, llm_response = handle_clarification(
        llm_response, user_prompt, formatted_history, conversation_id, user_id, history_manager)

    if not user_prompt:
        logger.warning("Empty prompt after clarification handling")
        return None  # If there's an error, return None

    # Use the potentially updated categories from the clarification response
    subcategories = llm_response.get("subcategories", [])
    logger.info(f"Identified subcategories: {subcategories}")

    logger.info("Fetching POI data from API")
    candidates = get_poi_data(
        latitude, longitude, search_radius, subcategories)
    if not candidates:
        logger.warning("No POIs found for given criteria")
        print("No POIs found based on your criteria.")
        return None
    logger.debug(f"Found {len(candidates)} POI candidates")

    logger.info("Selecting top candidates")
    top_candidates = find_top_candidates(
        candidates, latitude, longitude, search_radius, num_candidates)
    if not isinstance(top_candidates, dict):
        logger.debug("Converting top candidates to default format")
        top_candidates = {"default": top_candidates}

    logger.info(f"Returning {len(top_candidates)} top candidates")
    return top_candidates


def main():
    user_id = "test_user"  # Default user id for history tracking
    logger_instance.initialize_logging_context(user_id, 'api_execution')
    logger = logger_instance.get_logger()
    logger.info("Application startup")

    history_manager = HistoryManager()
    logger.debug("History manager initialized")

    conversation_id_input = input(
        "Enter conversation ID (or '0' for a new conversation): ").strip()

    if conversation_id_input == "0":
        # Create a new conversation
        conversation_id = history_manager.create_conversation(user_id)
        logger.info(f"Created new conversation: {conversation_id}")
    else:
        # Use an existing conversation ID
        conversation_id = conversation_id_input

        if os.path.exists(history_manager.get_conversation_file_path(user_id, conversation_id)):
            logger.info(
                f"Using existing conversation with ID: {conversation_id}")
            print(f"Using existing conversation with ID: {conversation_id}")
        else:
            logger.warning(
                f"Conversation ID {conversation_id} not found. Creating a new one.")
            print(
                f"Conversation ID {conversation_id} not found. Creating a new one.")
            conversation_id = history_manager.create_conversation(user_id)

    messages = history_manager.get_messages(user_id, conversation_id)
    if messages:
        logger.debug(f"Found {len(messages)} historical messages")
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
        logger.debug("No conversation history found")
        print("No previous messages in this conversation.")

    # Default location parameters
    latitude = 41.064108
    longitude = 29.031473
    search_radius = 2000
    num_candidates = 2
    logger.info(
        f"Using default location: {latitude},{longitude} with radius {search_radius}m")

    top_candidates = None
    reuse_prompt = False
    last_prompt = ""

    while True:
        if not reuse_prompt:
            user_prompt = input(
                "\nEnter your prompt (or type 'exit' to quit): ")
            if user_prompt.lower() == 'exit':
                logger.info("User initiated exit")
                break
            last_prompt = user_prompt
            logger.debug(f"User input received: {user_prompt}")
        else:
            user_prompt = last_prompt
            reuse_prompt = False
            logger.info(f"Reusing previous prompt: {user_prompt}")
            print(f"\nReusing last prompt: {user_prompt}")

        formatted_history = history_manager.get_formatted_history(
            user_id, conversation_id)
        logger.debug("Formatted history retrieved")

        # If we don't have top candidates yet, process a new query
        if not top_candidates:
            logger.info("Initiating new query processing")
            top_candidates = process_new_query(user_prompt, formatted_history, conversation_id,
                                               user_id, history_manager, latitude, longitude, search_radius, num_candidates)
            if not top_candidates:
                logger.warning("Query processing failed, continuing loop")
                continue

        # Get location advice based on the top candidates
        try:
            logger.info("Generating location advice")
            location_advice = get_location_advice(user_prompt, formatted_history, top_candidates,
                                                  latitude, longitude, search_radius)
            logger.debug(f"Location advice received: {location_advice}")
        except Exception as e:
            logger.error(f"Location advice error: {str(e)}")
            print(f"Error during location advice processing: {e}")
            continue

        response_text = location_advice.get(
            "response", "No response received.")
        # Save the assistant's response to history
        history_manager.add_assistant_message(
            user_id, conversation_id, response_text)
        logger.info("Assistant response added to history")
        print("\nLocation Advice:", response_text)

        # Ask for follow-up input regardless of the continuation value
        user_prompt = input(
            "\nEnter follow-up question (or type 'new' to start new search): ")
        if user_prompt.lower() == 'exit':
            logger.info("User exited during follow-up")
            break
        logger.debug(f"Follow-up input: {user_prompt}")

        # Save follow-up question and refresh history
        history_manager.add_user_message(user_id, conversation_id, user_prompt)
        formatted_history = history_manager.get_formatted_history(
            user_id, conversation_id)
        logger.debug("Updated history with follow-up question")

        # Get second location advice with the follow-up question
        try:
            logger.info("Processing follow-up location advice")
            location_advice = get_location_advice(user_prompt, formatted_history, top_candidates,
                                                  latitude, longitude, search_radius)
        except Exception as e:
            logger.error(f"Follow-up processing error: {str(e)}")
            print(f"Error during location advice processing: {e}")
            continue

        continuation = str(location_advice.get(
            "continuation", "false")).lower()
        response_text = location_advice.get(
            "response", "No response received.")
        history_manager.add_assistant_message(
            user_id, conversation_id, response_text)
        logger.info("Follow-up response added to history")
        if continuation == "true":
            print("\nLocation Advice:", response_text)

        # Now check if we should enter the continuation loop
        while continuation == "true":
            logger.info("Entering continuation loop")
            user_prompt = input(
                "\nEnter your follow up question2 (or type 'exit' to quit): ")
            if user_prompt.lower() == 'exit':
                logger.info("User exited during continuation loop")
                break
            last_prompt = user_prompt  # Update the last prompt
            logger.debug(f"Continuation input: {user_prompt}")

            # Save the new prompt and refresh history
            history_manager.add_user_message(
                user_id, conversation_id, user_prompt)
            formatted_history = history_manager.get_formatted_history(
                user_id, conversation_id)
            logger.debug("Updated history with continuation question")

            try:
                logger.info("Processing continuation request")
                location_advice = get_location_advice(user_prompt, formatted_history, top_candidates,
                                                      latitude, longitude, search_radius)
            except Exception as e:
                logger.error(f"Continuation processing error: {str(e)}")
                print(f"Error during location advice processing: {e}")
                continue

            continuation = str(location_advice.get(
                "continuation", "false")).lower()
            response_text = location_advice.get(
                "response", "No response received.")
            history_manager.add_assistant_message(
                user_id, conversation_id, response_text)
            logger.info("Continuation response added to history")

            if continuation == "true":
                print("\nLocation Advice:", response_text)
            else:
                logger.info("Continuation loop ending")
                break

        if continuation == "false":
            logger.info("Resetting candidates for new context")
            print("Starting new recommendation context with the same prompt.")
            top_candidates = None
            reuse_prompt = True

    logger.info("Application shutdown")


if __name__ == "__main__":
    main()
