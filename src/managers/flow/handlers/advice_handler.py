# src/managers/flow/handlers/advice_handler.py

from typing import Dict, Any, Optional
from src.managers.state.state_manager import StateManager
from src.managers.history.history_manager import HistoryManager
from src.get_location_advice import get_location_advice
from src.utils import convert_nan_to_none
from src.managers.flow.handlers.base_handler import BaseHandler


class AdviceHandler(BaseHandler):
    """
    Handler for processing advice continuation.
    """

    def __init__(self, state_manager: StateManager, history_manager: HistoryManager, num_candidates: Optional[int] = None):
        """
        Initialize the advice handler.

        Args:
            state_manager: Manager for storing and retrieving session state
            history_manager: Manager for logging conversation history
            num_candidates: Optional number of top candidates to return
        """
        super().__init__(state_manager, history_manager)
        self.num_candidates = num_candidates

    def handle_advice_continuation(self, user_id: str, session_id: str, user_input: str,
                                   formatted_history: str, session_data: Dict[str, Any],
                                   session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the advice continuation state when providing additional information.
        """
        self.logger.info(
            f"Processing advice continuation for session {session_id}")

        # Get the conversation to update process information
        conversation = self.history_manager._get_conversation(
            user_id, session_id)
        if not conversation["messages"]:
            return {"response": "Error: No message found", "status": "error"}

        last_message = conversation["messages"][-1]

        # Get stored parameters
        latitude = session_data.get("latitude")
        longitude = session_data.get("longitude")
        search_radius = session_data.get("search_radius")
        top_candidates = session_data.get("top_candidates", {})

        try:
            # Get follow-up advice
            advice_result = get_location_advice(user_input, formatted_history, top_candidates,
                                                latitude, longitude, search_radius)

            # Store advice process information
            last_message["processes"]["hidden"]["get_location_advice_result"] = advice_result

            # Check advice result format
            if "response" in advice_result:
                # Standard response
                response_text = advice_result.get("response")
                continuation = str(advice_result.get(
                    "continuation", "false")).lower() == "true"

                # Log assistant response
                self.history_manager.log_assistant_message(
                    user_id, session_id, response_text,
                    {
                        "status": "advice_provided",
                        "continuation": continuation,
                        "top_candidate_result": top_candidates
                    }
                )

                # If not continuing, set state back to new_query
                if not continuation:
                    session["current_state"] = "new_query"
                    self.state_manager.save_session(
                        user_id, session_id, session)

                return convert_nan_to_none({
                    "response": response_text,
                    "status": "advice_provided",
                    "continuation": continuation,
                    "top_candidates": top_candidates
                })
            elif "action" in advice_result and advice_result["action"] == "classification_agent":
                # Handle new search with specific location
                new_prompt = advice_result.get("prompt", user_input)
                new_latitude = advice_result.get("latitude", latitude)
                new_longitude = advice_result.get("longitude", longitude)
                new_radius = advice_result.get("radius", search_radius)

                # Import the query handler here to avoid circular imports
                from src.managers.flow.handlers.query_handler import QueryHandler
                query_handler = QueryHandler(
                    self.state_manager, self.history_manager, self.num_candidates)

                # Directly search with the new location parameters
                return query_handler.direct_location_search(
                    user_id,
                    session_id,
                    new_prompt,
                    new_latitude,
                    new_longitude,
                    new_radius,
                    session,
                    formatted_history
                )
            else:
                self.logger.warning(
                    "Unknown response format from location advice")
                session["current_state"] = "new_query"
                self.state_manager.save_session(user_id, session_id, session)

                return convert_nan_to_none({
                    "response": "I couldn't process your request properly. Let's try again with a new query.",
                    "status": "error",
                    "top_candidates": {}
                })

        except Exception as e:
            self.logger.error(f"Location advice error: {str(e)}")
            session["current_state"] = "new_query"
            self.state_manager.save_session(user_id, session_id, session)

            return convert_nan_to_none({
                "response": f"I encountered an error while processing your request: {str(e)}. Let's try again.",
                "status": "error",
                "top_candidates": {}
            })
