# src/managers/flow/handlers/clarification_handler.py

from typing import Dict, Any
from src.managers.state.state_manager import StateManager
from src.managers.history.history_manager import HistoryManager
from src.managers.flow.handlers.base_handler import BaseHandler


class ClarificationHandler(BaseHandler):
    """
    Handler for processing clarification requests.
    """

    def __init__(self, state_manager: StateManager, history_manager: HistoryManager):
        """
        Initialize the clarification handler.

        Args:
            state_manager: Manager for storing and retrieving session state
            history_manager: Manager for logging conversation history
        """
        super().__init__(state_manager, history_manager)

    def handle_clarification(self, user_id: str, session_id: str, user_input: str,
                             formatted_history: str, session_data: Dict[str, Any],
                             session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the clarification state when LLM needs more information.

        Args:
            user_id: Unique identifier for the user
            session_id: Unique identifier for the current session
            user_input: Text message from the user
            formatted_history: Formatted conversation history
            session_data: Current session data
            session: Current session state

        Returns:
            Dict containing response and any additional action information
        """
        self.logger.info(f"Processing clarification for session {session_id}")

        # Get stored parameters
        latitude = session_data.get("latitude")
        longitude = session_data.get("longitude")
        search_radius = session_data.get("search_radius")

        # Set state back to new_query to re-process with clarification
        session["current_state"] = "new_query"
        self.state_manager.save_session(user_id, session_id, session)

        # Import the query handler here to avoid circular imports
        from src.managers.flow.handlers.query_handler import QueryHandler
        query_handler = QueryHandler(self.state_manager, self.history_manager)

        # Process with the clarification input as a new query
        return query_handler.process_query(
            user_id, session_id, user_input, formatted_history,
            latitude, longitude, search_radius, session
        )
