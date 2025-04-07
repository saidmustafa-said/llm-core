# flow_manager.py

from typing import Dict, Any, Optional, Tuple
from src.managers.state.state_manager import StateManager
from src.managers.history.history_manager import HistoryManager
from src.data_types import TopCandidates
from src.get_location_advice import get_location_advice
from src.get_top_candidates import find_top_candidates
from src.poi_filter import POIManager
from src.llamarequest import llm_api
from src.logger_setup import logger_instance


class FlowManager:
    """
    Controls the user journey flow through the application,
    managing state transitions and history logging.
    """

    def __init__(self, state_manager: StateManager, history_manager: HistoryManager):
        """
        Initialize the FlowManager with state and history managers.

        Args:
            state_manager: Manager for storing and retrieving session state
            history_manager: Manager for logging conversation history
        """
        self.state_manager = state_manager
        self.history_manager = history_manager
        self.poi_manager = POIManager()
        self.logger = logger_instance.get_logger()

    def process_user_input(self, user_id: str, session_id: str, user_input: str,
                           latitude: float = 40.971255, longitude: float = 28.793878,
                           search_radius: int = 1000) -> Dict[str, Any]:
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
        # Log the user message
        self.history_manager.log_user_message(user_id, session_id, user_input)

        # Get or create a session state
        session = self.state_manager.get_session(user_id, session_id)
        if not session:
            self.logger.warning(
                f"Session {session_id} not found, creating new session")
            session_id = self.state_manager.create_session(user_id)
            session = self.state_manager.get_session(user_id, session_id)

        # Get current state from session
        current_state = session.get("current_state", "initial")
        session_data = session.get("data", {})

        # Get conversation history
        formatted_history = self.history_manager.get_formatted_history(
            user_id, session_id)

        # Process based on current state
        if current_state == "initial" or current_state == "new_query":
            return self._handle_classification(user_id, session_id, user_input, formatted_history,
                                               latitude, longitude, search_radius, session)
        elif current_state == "providing_advice":
            return self._handle_advice_continuation(user_id, session_id, user_input, formatted_history,
                                                    session_data, session)
        elif current_state == "clarification_needed":
            return self._handle_clarification(user_id, session_id, user_input, formatted_history,
                                              session_data, session)
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

    def _handle_classification(self, user_id: str, session_id: str, user_input: str,
                               formatted_history: str, latitude: float, longitude: float,
                               search_radius: int, session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the classification state for a new query"""
        self.logger.info(f"Processing classification for session {session_id}")

        # Get POI subcategories for LLM context
        subcategories = self.poi_manager.get_poi_data(
            latitude, longitude, search_radius)

        # Call LLM for classification
        extracted_json = llm_api(user_input, formatted_history, subcategories)

        # Check if clarification is needed
        if "clarification" in extracted_json:
            clarification_value = extracted_json.get("clarification")

            # Handle different clarification formats
            question = ""
            if isinstance(clarification_value, str):
                question = clarification_value
            elif isinstance(clarification_value, dict) and "question" in clarification_value:
                question = clarification_value.get("question", "")
            else:
                question = "Please provide more information"

            # Update session state for clarification
            session["current_state"] = "clarification_needed"
            session["data"] = {
                "original_prompt": user_input,
                "clarification_question": question,
                "latitude": latitude,
                "longitude": longitude,
                "search_radius": search_radius
            }
            self.state_manager.save_session(user_id, session_id, session)

            # Log assistant's clarification request
            self.history_manager.log_assistant_message(
                user_id, session_id, question)

            return {
                "response": question,
                "status": "clarification_needed"
            }

        # Check for subcategories to search
        if "subcategories" in extracted_json and "tags" in extracted_json:
            subcategories = extracted_json.get("subcategories", [])
            self.logger.info(f"Identified subcategories: {subcategories}")

            # Get POI data for identified subcategories
            candidates = self.poi_manager.get_poi_data(
                latitude, longitude, search_radius, subcategories)

            if not candidates:
                self.logger.warning("No POIs found for given criteria")
                # Update session state
                session["current_state"] = "new_query"
                self.state_manager.save_session(user_id, session_id, session)

                response_text = "I couldn't find any places matching your criteria. Could you try with different criteria or a wider search radius?"
                self.history_manager.log_assistant_message(
                    user_id, session_id, response_text)

                return {
                    "response": response_text,
                    "status": "no_results"
                }

            # Find top candidates
            num_candidates = 4  # Default value
            top_candidates = find_top_candidates(
                candidates, latitude, longitude, search_radius, num_candidates)

            if not isinstance(top_candidates, dict):
                top_candidates = {"default": top_candidates}

            # Get location advice for top candidates
            try:
                advice_result = get_location_advice(user_input, formatted_history, top_candidates,
                                                    latitude, longitude, search_radius)

                # Update session state
                session["current_state"] = "providing_advice"
                session["data"] = {
                    "prompt": user_input,
                    "top_candidates": top_candidates,
                    "extracted_json": extracted_json,
                    "latitude": latitude,
                    "longitude": longitude,
                    "search_radius": search_radius
                }
                self.state_manager.save_session(user_id, session_id, session)

                # Check advice result format
                if "response" in advice_result:
                    # Standard response
                    response_text = advice_result.get("response")
                    continuation = str(advice_result.get(
                        "continuation", "false")).lower() == "true"

                    # Log assistant response
                    self.history_manager.log_assistant_message(
                        user_id, session_id, response_text)

                    return {
                        "response": response_text,
                        "status": "advice_provided",
                        "continuation": continuation
                    }
                elif "action" in advice_result and advice_result["action"] == "classification_agent":
                    # Special case: new classification request
                    new_parameters = {
                        "prompt": advice_result.get("prompt", user_input),
                        "longitude": advice_result.get("longitude", longitude),
                        "latitude": advice_result.get("latitude", latitude),
                        "radius": advice_result.get("radius", search_radius)
                    }

                    # Update state for new query
                    session["current_state"] = "new_query"
                    session["data"] = new_parameters
                    self.state_manager.save_session(
                        user_id, session_id, session)

                    return {
                        "response": f"Starting new search with coordinates: {new_parameters['latitude']}, {new_parameters['longitude']} and radius: {new_parameters['radius']}m",
                        "status": "new_classification",
                        "parameters": new_parameters
                    }
                else:
                    self.logger.warning(
                        "Unknown response format from location advice")
                    return {
                        "response": "I couldn't process your request properly. Let's try again with a new query.",
                        "status": "error"
                    }

            except Exception as e:
                self.logger.error(f"Location advice error: {str(e)}")
                session["current_state"] = "new_query"
                self.state_manager.save_session(user_id, session_id, session)

                return {
                    "response": f"I encountered an error while processing your request: {str(e)}. Let's try again.",
                    "status": "error"
                }
        else:
            self.logger.warning("No subcategories found in LLM response")
            session["current_state"] = "new_query"
            self.state_manager.save_session(user_id, session_id, session)

            response_text = "I couldn't identify what you're looking for. Could you be more specific about the type of place you want to find?"
            self.history_manager.log_assistant_message(
                user_id, session_id, response_text)

            return {
                "response": response_text,
                "status": "no_subcategories"
            }

    def _handle_clarification(self, user_id: str, session_id: str, user_input: str,
                              formatted_history: str, session_data: Dict[str, Any],
                              session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the clarification state when LLM needs more information"""
        self.logger.info(f"Processing clarification for session {session_id}")

        # Get stored parameters
        latitude = session_data.get("latitude", 40.971255)
        longitude = session_data.get("longitude", 28.793878)
        search_radius = session_data.get("search_radius", 1000)

        # Set state back to new_query to re-process with clarification
        session["current_state"] = "new_query"
        self.state_manager.save_session(user_id, session_id, session)

        # Process with the clarification input as a new query
        return self._handle_classification(user_id, session_id, user_input, formatted_history,
                                           latitude, longitude, search_radius, session)

    def _handle_advice_continuation(self, user_id: str, session_id: str, user_input: str,
                                    formatted_history: str, session_data: Dict[str, Any],
                                    session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle continuations when user asks follow-up questions about locations"""
        self.logger.info(
            f"Processing advice continuation for session {session_id}")

        # Get stored parameters
        top_candidates = session_data.get("top_candidates", {})
        latitude = session_data.get("latitude", 40.971255)
        longitude = session_data.get("longitude", 28.793878)
        search_radius = session_data.get("search_radius", 1000)

        try:
            # Get follow-up advice
            advice_result = get_location_advice(user_input, formatted_history, top_candidates,
                                                latitude, longitude, search_radius)

            # Check advice result format
            if "response" in advice_result:
                # Standard response
                response_text = advice_result.get("response")
                continuation = str(advice_result.get(
                    "continuation", "false")).lower() == "true"

                # Log assistant response
                self.history_manager.log_assistant_message(
                    user_id, session_id, response_text)

                # If not continuing, set state back to new_query
                if not continuation:
                    session["current_state"] = "new_query"
                    self.state_manager.save_session(
                        user_id, session_id, session)

                return {
                    "response": response_text,
                    "status": "advice_provided",
                    "continuation": continuation
                }
            elif "action" in advice_result and advice_result["action"] == "classification_agent":
                # Special case: new classification request
                new_parameters = {
                    "prompt": advice_result.get("prompt", user_input),
                    "longitude": advice_result.get("longitude", longitude),
                    "latitude": advice_result.get("latitude", latitude),
                    "radius": advice_result.get("radius", search_radius)
                }

                # Update state for new query
                session["current_state"] = "new_query"
                session["data"] = new_parameters
                self.state_manager.save_session(user_id, session_id, session)

                return {
                    "response": f"Starting new search with coordinates: {new_parameters['latitude']}, {new_parameters['longitude']} and radius: {new_parameters['radius']}m",
                    "status": "new_classification",
                    "parameters": new_parameters
                }
            else:
                self.logger.warning(
                    "Unknown response format from location advice")
                session["current_state"] = "new_query"
                self.state_manager.save_session(user_id, session_id, session)

                return {
                    "response": "I couldn't process your request properly. Let's try again with a new query.",
                    "status": "error"
                }

        except Exception as e:
            self.logger.error(f"Location advice error: {str(e)}")
            session["current_state"] = "new_query"
            self.state_manager.save_session(user_id, session_id, session)

            return {
                "response": f"I encountered an error while processing your request: {str(e)}. Let's try again.",
                "status": "error"
            }

    def create_new_session(self, user_id: str) -> str:
        """Create a new session and return the session ID"""
        self.logger.info(f"Creating new session for user {user_id}")
        return self.state_manager.create_session(user_id)
