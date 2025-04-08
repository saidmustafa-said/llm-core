# main.py

from typing import Dict, Any, Optional, Tuple
from src.managers.state.state_manager import StateManager
from src.managers.history.history_manager import HistoryManager
from src.flow_manager import FlowManager
from src.logger_setup import session_logger, get_logger


def process_request(user_id: str, session_id: str, user_input: str,
                    latitude: float = 40.971255, longitude: float = 28.793878,
                    search_radius: int = 1000,
                    state_manager: Optional[StateManager] = None,
                    history_manager: Optional[HistoryManager] = None) -> Dict[str, Any]:
    """
    Process a user request through the system.

    This is the main entry point for the application logic.

    Args:
        user_id: Unique identifier for the user
        session_id: Unique identifier for the current session
        user_input: Text message from the user
        latitude: User's current latitude
        longitude: User's current longitude
        search_radius: Search radius in meters for POIs
        state_manager: Optional state manager instance (if not provided, one will be created)
        history_manager: Optional history manager instance (if not provided, one will be created)

    Returns:
        Dict containing response and any additional action information
    """
    logger = get_logger()
    logger.info(f"Processing request for user {user_id}, session {session_id}")

    # If managers are not provided, use default JSON implementations
    if state_manager is None:
        from src.managers.state.json_state_manager import JSONStateManager
        state_manager = JSONStateManager()
        logger.debug("Created default JSONStateManager")

    if history_manager is None:
        from src.managers.history.json_history_manager import JSONHistoryManager
        history_manager = JSONHistoryManager()
        logger.debug("Created default JSONHistoryManager")

    # Create flow manager
    flow_manager = FlowManager(state_manager, history_manager)

    # Process the request - all logic now handled in flow_manager
    return flow_manager.process_user_input(
        user_id, session_id, user_input, latitude, longitude, search_radius
    )


def create_session(user_id: str, state_manager: Optional[StateManager] = None) -> str:
    """
    Create a new session for a user.

    Args:
        user_id: Unique identifier for the user
        state_manager: Optional state manager instance (if not provided, one will be created)

    Returns:
        New session ID
    """
    logger = get_logger()
    logger.info(f"Creating new session for user {user_id}")

    # If state manager is not provided, use default JSON implementation
    if state_manager is None:
        from src.managers.state.json_state_manager import JSONStateManager
        state_manager = JSONStateManager()
        logger.debug("Created default JSONStateManager")

    # Create flow manager
    from src.managers.history.json_history_manager import JSONHistoryManager
    history_manager = JSONHistoryManager()
    flow_manager = FlowManager(state_manager, history_manager)

    # Create new session
    session_id = flow_manager.create_new_session(user_id)
    logger.info(f"Created session ID: {session_id} for user: {user_id}")

    return session_id


def get_session_history(user_id: str, session_id: str, history_manager: Optional[HistoryManager] = None) -> str:
    """
    Get formatted history for a session.

    Args:
        user_id: Unique identifier for the user
        session_id: Unique identifier for the session
        history_manager: Optional history manager instance (if not provided, one will be created)

    Returns:
        Formatted history string
    """
    logger = get_logger()
    logger.info(f"Getting history for user {user_id}, session {session_id}")

    # If history manager is not provided, use default JSON implementation
    if history_manager is None:
        from src.managers.history.json_history_manager import JSONHistoryManager
        history_manager = JSONHistoryManager()
        logger.debug("Created default JSONHistoryManager")

    return history_manager.get_formatted_history(user_id, session_id)


def get_session_messages(user_id: str, session_id: str, history_manager: Optional[HistoryManager] = None) -> list:
    """
    Get raw messages for a session.

    Args:
        user_id: Unique identifier for the user
        session_id: Unique identifier for the session
        history_manager: Optional history manager instance (if not provided, one will be created)

    Returns:
        List of message dictionaries
    """
    logger = get_logger()
    logger.info(f"Getting messages for user {user_id}, session {session_id}")

    # If history manager is not provided, use default JSON implementation
    if history_manager is None:
        from src.managers.history.json_history_manager import JSONHistoryManager
        history_manager = JSONHistoryManager()
        logger.debug("Created default JSONHistoryManager")

    return history_manager.get_history(user_id, session_id)


# # Command line interface for testing (will be replaced by API)
# if __name__ == "__main__":
#     user_id = "test_user"

#     # Create managers
#     from src.managers.state.json_state_manager import JSONStateManager
#     from src.managers.history.json_history_manager import JSONHistoryManager
#     state_manager = JSONStateManager()
#     history_manager = JSONHistoryManager()

#     # Create flow manager
#     flow_manager = FlowManager(state_manager, history_manager)

#     # Get or create session
#     conversation_id_input = input(
#         "Enter session ID (or '0' for a new session): ").strip()

#     if conversation_id_input == "0":
#         # Create a new session
#         session_id = flow_manager.create_new_session(user_id)
#         print(f"Created new session with ID: {session_id}")
#     else:
#         # Use existing session
#         session_id = conversation_id_input
#         session = state_manager.get_session(user_id, session_id)
#         if session:
#             print(f"Using existing session with ID: {session_id}")
#         else:
#             print(f"Session ID {session_id} not found. Creating a new one.")
#             session_id = flow_manager.create_new_session(user_id)
#     session_logger.start_session(user_id, session_id)
#     logger = get_logger()
#     # Show history
#     messages = history_manager.get_history(user_id, session_id)
#     if messages:
#         print("\n--- Conversation History ---")
#         for msg in messages:
#             event_type = msg.get("type", "unknown")
#             content = msg.get("content", "")

#             if event_type == "user_message":
#                 print(f"User: {content}")
#             elif event_type == "assistant_message":
#                 print(f"Bot: {content}")
#         print("--- End of History ---\n")
#     else:
#         print("No previous messages in this session.")

#     # Default parameters
#     latitude = 40.971255
#     longitude = 28.793878
#     search_radius = 1000

#     # Add flag to track if we need user input
#     need_user_input = True
#     user_input = ""

#     # Main interaction loop
#     while True:
#         # Get user input only if needed
#         if need_user_input:
#             user_input = input(
#                 "\nEnter your prompt (or type 'exit' to quit): ")
#             if user_input.lower() == 'exit':
#                 break
#             need_user_input = True  # Reset flag for next loop

#         # Process request
#         response = flow_manager.process_user_input(
#             user_id, session_id, user_input, latitude, longitude, search_radius
#         )

#         # Print response
#         print(f"\nResponse: {response.get('response', 'No response')}")

#         # Handle parameter changes and determine if we need new input
#         if response.get("status") == "new_classification" and "parameters" in response:
#             params = response["parameters"]
#             # Update parameters for new search
#             user_input = params.get("prompt", user_input)
#             latitude = params.get("latitude", latitude)
#             longitude = params.get("longitude", longitude)
#             search_radius = params.get("radius", search_radius)

#             print(
#                 f"Updated parameters: lat={latitude}, lon={longitude}, radius={search_radius}")
#             print(f"Starting new search with prompt: '{user_input}'")

#             # Don't ask for new input since we're using the prompt from the LLM
#             need_user_input = False

#             # Continue the loop to process with new parameters
#             continue

#         # For next iteration, get new user input (unless overridden by parameter change)
#         need_user_input = True
