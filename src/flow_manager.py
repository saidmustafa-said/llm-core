# src/managers/flow/flow_manager.py

from typing import Dict, Any, Optional
from src.managers.state.state_manager import StateManager
from src.managers.history.history_manager import HistoryManager
from src.managers.flow.handlers.query_handler import QueryHandler
from src.managers.flow.handlers.advice_handler import AdviceHandler
from src.managers.flow.handlers.clarification_handler import ClarificationHandler
from src.logger_setup import get_logger


class FlowManager:
    """
    Controls the user journey flow through the application,
    managing state transitions and history logging.
    """

    def __init__(self, state_manager: StateManager, history_manager: HistoryManager, num_candidates: Optional[int] = None):
        """
        Initialize the FlowManager with state and history managers.

        Args:
            state_manager: Manager for storing and retrieving session state
            history_manager: Manager for logging conversation history
            num_candidates: Optional number of top candidates to return
        """
        self.state_manager = state_manager
        self.history_manager = history_manager
        self.logger = get_logger()
        self.num_candidates = num_candidates

        # Initialize handlers with shared references
        self.query_handler = QueryHandler(
            state_manager, history_manager, num_candidates)
        self.advice_handler = AdviceHandler(
            state_manager, history_manager, num_candidates)
        self.clarification_handler = ClarificationHandler(
            state_manager, history_manager)

    def process_user_input(self, user_id: str, session_id: str, user_input: str,
                           latitude: float, longitude: float,
                           search_radius: int) -> Dict[str, Any]:
        """
        Process a user input message and return the appropriate response.

        Args:
            user_id: Unique identifier for the user
            session_id: Unique identifier for the current session
            user_input: Text message from the user
            latitude: User's current latitude
            longitude: User's current longitude
            search_radius: Search radius in meters for POIs

        Returns:
            Dict containing response and any additional action information
        """
        # Get or create a session state
        session = self.state_manager.get_session(user_id, session_id)
        if not session:
            self.logger.warning(
                f"Session {session_id} not found, creating new session")
            session_id = self.state_manager.create_session(user_id)
            session = self.state_manager.get_session(user_id, session_id)

        # Get current state from session
        current_state = session.get("current_state")
        if current_state is None:
            current_state = "initial"
        session_data = session.get("data", {})

        # Get conversation history
        formatted_history = self.history_manager.get_formatted_history(
            user_id, session_id)

        # Process based on current state
        if current_state == "initial" or current_state == "new_query":
            return self.query_handler.process_query(
                user_id, session_id, user_input, formatted_history,
                latitude, longitude, search_radius, session
            )
        elif current_state == "providing_advice":
            return self.advice_handler.handle_advice_continuation(
                user_id, session_id, user_input, formatted_history,
                session_data, session
            )
        elif current_state == "clarification_needed":
            return self.clarification_handler.handle_clarification(
                user_id, session_id, user_input, formatted_history,
                session_data, session
            )
        else:
            # Unknown state, reset to initial
            self.logger.warning(
                f"Unknown state: {current_state}, resetting to initial")
            session["current_state"] = "initial"
            self.state_manager.save_session(user_id, session_id, session)
            return {
                "response": "I seem to have lost track of our conversation. Let's start over. What can I help you find?",
                "status": "reset"
            }

    def create_new_session(self, user_id: str) -> str:
        """Create a new session and return the session ID"""
        self.logger.info(f"Creating new session for user {user_id}")
        return self.state_manager.create_session(user_id)

    def delete_session(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Delete a session by marking its history and state files as removed.

        Args:
            user_id: Unique identifier for the user
            session_id: Unique identifier for the session to delete

        Returns:
            Dict containing:
            - status: str - "success" or "error"
            - message: str - Description of the result
        """
        try:
            # Delete history
            self.history_manager.delete_history(user_id, session_id)

            # Delete session state
            self.state_manager.delete_session(user_id, session_id)

            self.logger.info(
                f"Successfully marked session {session_id} as removed for user {user_id}")
            return {
                "status": "success",
                "message": f"Session {session_id} has been marked as removed"
            }
        except Exception as e:
            self.logger.error(f"Error marking session as removed: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to mark session as removed: {str(e)}"
            }
