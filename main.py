# main.py

from typing import Dict, Any, Optional, Tuple
from src.managers.state.state_manager import StateManager
from src.managers.history.history_manager import HistoryManager
from src.flow_manager import FlowManager
from src.logger_setup import session_logger, get_logger


def process_request(user_id: str, session_id: str, user_input: str,
                    latitude: float, longitude: float,
                    search_radius: int,
                    state_manager: Optional[StateManager] = None,
                    history_manager: Optional[HistoryManager] = None,
                    num_candidates: int = 4) -> Dict[str, Any]:
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
        num_candidates: Number of top candidates to return (default: 4)

    Returns:
        Dict containing:
        - response: str - The text response to the user
        - status: str - The current state of the conversation
        - continuation: bool - Whether the conversation should continue
        - top_candidates: Dict[str, List[POIData]] - The top candidates found for the query
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
    flow_manager = FlowManager(state_manager, history_manager, num_candidates)

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
