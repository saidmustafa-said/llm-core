from src.data_types import LLMResponse, TopCandidates
from src.get_location_advice import get_location_advice
from src.get_top_candidates import find_top_candidates
from src.poi_filter import POIManager
from src.llamarequest import llm_api
from src.history_manager import HistoryManager
import os
from src.logger_setup import logger_instance

poi_manager = POIManager()


def handle_clarification_loop(prompt: str, formatted_history: str, conversation_id: str, user_id: str, history_manager: HistoryManager, user_lat, user_lon, search_radius) -> tuple:
    """
    Handles any clarification needed from the LLM response in a while loop.
    Returns a tuple of (updated_prompt, extracted_json)
    """
    logger = logger_instance.get_logger()
    logger.info("Initiating LLM API call")

    subcategories = poi_manager.get_poi_data(
        user_lat, user_lon, search_radius)
    # Initial LLM call
    extracted_json = llm_api(prompt, formatted_history, subcategories)
    logger.debug(f"LLM response received: {extracted_json}")

    # Enter clarification loop if needed
    while "clarification" in extracted_json:
        clarification_value = extracted_json.get("clarification")

        # Handle different clarification formats
        question = ""
        if isinstance(clarification_value, str):
            question = clarification_value
        elif isinstance(clarification_value, dict) and "question" in clarification_value:
            question = clarification_value.get("question", "")
        else:
            question = "Please provide more information"

        logger.info(
            f"Clarification requested for conversation {conversation_id}: {question}")
        print(f"\nClarification Needed: {question}")

        # Get user clarification input
        additional_input = input("Provide clarification: ")
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

        subcategories = poi_manager.get_poi_data(
            user_lat, user_lon, search_radius)
        extracted_json = llm_api(
            additional_input, formatted_history, subcategories)
        logger.debug(f"Clarification response received: {extracted_json}")

        # Update the prompt to reflect the new input
        prompt = additional_input

    logger.info("Clarification handling complete")
    return prompt, extracted_json


def process_classification(user_prompt: str, formatted_history: str, conversation_id: str,
                           user_id: str, history_manager: HistoryManager,
                           latitude: float, longitude: float, search_radius: int,
                           num_candidates: int) -> tuple:
    """
    Process a classification request to get candidates.
    Returns a tuple of (top_candidates, updated_prompt, extracted_json)
    """
    logger = logger_instance.get_logger()
    logger.info(f"Processing new query for conversation {conversation_id}")

    # Save the user message to history
    history_manager.add_user_message(user_id, conversation_id, user_prompt)
    logger.debug("User message added to history")

    # Handle LLM API call with clarification loop
    updated_prompt, extracted_json = handle_clarification_loop(
        user_prompt, formatted_history, conversation_id, user_id, history_manager, latitude, longitude, search_radius)

    if not extracted_json or "error" in extracted_json:
        logger.error("LLM processing error occurred")
        print("Error in LLM processing. Please try again.")
        return None, updated_prompt, extracted_json

    # Check if we have subcategories for POI search
    if "subcategories" in extracted_json and "tags" in extracted_json:
        subcategories = extracted_json.get("subcategories", [])
        logger.info(f"Identified subcategories: {subcategories}")

        logger.info("Fetching POI data from API")
        candidates = poi_manager.get_poi_data(
            latitude, longitude, search_radius, subcategories)
        if not candidates:
            logger.warning("No POIs found for given criteria")
            print("No POIs found based on your criteria.")
            return None, updated_prompt, extracted_json

        logger.debug(f"Found {len(candidates)} POI candidates")

        logger.info("Selecting top candidates")
        top_candidates = find_top_candidates(
            candidates, latitude, longitude, search_radius, num_candidates)
        if not isinstance(top_candidates, dict):
            logger.debug("Converting top candidates to default format")
            top_candidates = {"default": top_candidates}

        logger.info(f"Returning {len(top_candidates)} top candidates")
        return top_candidates, updated_prompt, extracted_json
    else:
        logger.warning("No subcategories found in LLM response")
        print("Could not identify search categories from your query.")
        return None, updated_prompt, extracted_json


def handle_location_advice_loop(user_prompt: str, formatted_history: str, top_candidates: TopCandidates,
                                latitude: float, longitude: float, search_radius: int,
                                conversation_id: str, user_id: str, history_manager: HistoryManager) -> tuple:
    """
    Handle the location advice loop, including continuations.
    Returns a tuple of (continue_current_flow, new_parameters) where new_parameters might contain
    new location parameters if a new classification agent action is triggered.
    """
    logger = logger_instance.get_logger()

    try:
        logger.info("Generating location advice")
        extracted_json = get_location_advice(user_prompt, formatted_history, top_candidates,
                                             latitude, longitude, search_radius)
        logger.debug(f"Location advice received: {extracted_json}")
    except Exception as e:
        logger.error(f"Location advice error: {str(e)}")
        print(f"Error during location advice processing: {e}")
        return True, None

    # Check for action type in response
    if "response" in extracted_json:
        # It's a continuation response
        response_text = extracted_json.get("response")
        continuation = str(extracted_json.get(
            "continuation", "false")).lower() == "true"

        # Save and display the response
        history_manager.add_assistant_message(
            user_id, conversation_id, response_text)
        logger.info("Assistant response added to history")
        print("\nLocation Advice:", response_text)

        if continuation:
            # Continue the current advice flow
            return True, None
        else:
            # End the current flow, start new search with same prompt
            return False, None

    elif "action" in extracted_json and extracted_json["action"] == "classification_agent":
        # It's a new search request with specific parameters
        logger.info("New classification request with parameters")

        # Extract the new parameters
        new_parameters = {
            "prompt": extracted_json.get("prompt", user_prompt),
            "longitude": extracted_json.get("longitude", longitude),
            "latitude": extracted_json.get("latitude", latitude),
            "radius": extracted_json.get("radius", search_radius)
        }

        # End current flow and start new search with new parameters
        return False, new_parameters
    else:
        logger.warning("Unknown response format")
        print("Received an unknown response format. Starting new search.")
        return False, None


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
    longitude = 28.793878
    latitude = 40.971255
    search_radius = 1000
    num_candidates = 4
    logger.info(
        f"Using default location: {latitude},{longitude} with radius {search_radius}m")

    # Flag to indicate if we need to get user input or use the existing one
    need_user_input = True
    user_prompt = ""

    while True:
        # Get user prompt only if needed
        if need_user_input:
            user_prompt = input(
                "\nEnter your prompt (or type 'exit' to quit): ")
            if user_prompt.lower() == 'exit':
                logger.info("User initiated exit")
                break
            logger.debug(f"User input received: {user_prompt}")
            need_user_input = False  # Reset the flag after getting input

        # Get formatted history
        formatted_history = history_manager.get_formatted_history(
            user_id, conversation_id)
        logger.debug("Formatted history retrieved")

        # Process new query to get classification and candidates
        top_candidates, user_prompt, extracted_json = process_classification(
            user_prompt, formatted_history, conversation_id, user_id, history_manager,
            latitude, longitude, search_radius, num_candidates)

        if not top_candidates:
            logger.warning("Classification processing failed, continuing loop")
            need_user_input = True  # Need new input since this one failed
            continue

        # Enter the location advice loop
        continue_current_flow = True
        while continue_current_flow:
            # Get formatted history again as it might have been updated
            formatted_history = history_manager.get_formatted_history(
                user_id, conversation_id)

            # Process location advice
            continue_current_flow, new_parameters = handle_location_advice_loop(
                user_prompt, formatted_history, top_candidates,
                latitude, longitude, search_radius,
                conversation_id, user_id, history_manager)

            if continue_current_flow:
                # Get next user prompt for continuation
                user_prompt = input(
                    "\nEnter follow-up question (or type 'exit' to quit): ")
                if user_prompt.lower() == 'exit':
                    logger.info("User exited during follow-up")
                    continue_current_flow = False
                    need_user_input = True  # Reset flag for next iteration
                    break

                # Save the new prompt to history
                history_manager.add_user_message(
                    user_id, conversation_id, user_prompt)
                logger.debug(f"Follow-up input saved: {user_prompt}")

        # Check if we have new parameters for the next search
        if new_parameters:
            logger.info("Updating parameters for new search")
            user_prompt = new_parameters.get("prompt")
            latitude = new_parameters.get("latitude")
            longitude = new_parameters.get("longitude")
            search_radius = new_parameters.get("radius")

            logger.info(
                f"New parameters: prompt='{user_prompt}', lat={latitude}, lon={longitude}, radius={search_radius}")
            print(
                f"\nStarting new search with coordinates: {latitude}, {longitude} and radius: {search_radius}m")

            # We already have a prompt from the LLM, don't ask for user input
            need_user_input = False
        else:
            # No new parameters, get fresh user input in the next iteration
            need_user_input = True

    logger.info("Application shutdown")


if __name__ == "__main__":
    main()
