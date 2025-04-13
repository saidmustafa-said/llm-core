# src/managers/flow/handlers/query_handler.py

from typing import Dict, Any, Optional
from src.managers.state.state_manager import StateManager
from src.managers.history.history_manager import HistoryManager
from src.get_location_advice import get_location_advice
from src.get_top_candidates import create_top_candidates_finder
from src.poi_filter import create_poi_manager, IPOIManager
from src.llamarequest import llm_api
from src.utils import convert_nan_to_none
from src.managers.flow.handlers.base_handler import BaseHandler
from src.interfaces.top_candidates import ITopCandidatesFinder


class QueryHandler(BaseHandler):
    """
    Handler for processing new queries and location searches.
    """

    def __init__(self, state_manager: StateManager, history_manager: HistoryManager, num_candidates: Optional[int] = None):
        """
        Initialize the query handler.

        Args:
            state_manager: Manager for storing and retrieving session state
            history_manager: Manager for logging conversation history
            num_candidates: Optional number of top candidates to return
        """
        super().__init__(state_manager, history_manager)
        self.poi_manager: IPOIManager = create_poi_manager()
        self.top_candidates_finder: ITopCandidatesFinder = create_top_candidates_finder()
        self.num_candidates = num_candidates

    def process_query(self, user_id: str, session_id: str, user_input: str,
                      formatted_history: str, latitude: float, longitude: float,
                      search_radius: int, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a new query, including handling classification and location search.

        Args:
            user_id: Unique identifier for the user
            session_id: Unique identifier for the current session
            user_input: Text message from the user
            formatted_history: Formatted conversation history
            latitude: User's current latitude
            longitude: User's current longitude
            search_radius: Search radius in meters for POIs
            session: Current session state

        Returns:
            Dict containing response and any additional action information
        """
        self.logger.info(f"Processing new query for session {session_id}")

        # Get the conversation to update process information
        conversation = self.history_manager._get_conversation(
            user_id, session_id)
        if not conversation["messages"]:
            return {"response": "Error: No message found", "status": "error"}

        last_message = conversation["messages"][-1]

        # Step 1: Get text classification from LLM
        subcategories_for_context = self.poi_manager.get_available_categories(
            latitude, longitude, search_radius)
        print("Subcategories for context:", subcategories_for_context)

        # Store process information
        last_message["processes"]["hidden"]["get_available_categories"] = subcategories_for_context
        # Save the conversation after updating process information
        self.history_manager._save_conversation(
            user_id, session_id, conversation)

        extracted_json = llm_api(user_input, subcategories_for_context)
        print("Extracted JSON:", extracted_json)

        # Store LLM process information
        last_message["processes"]["hidden"]["llamarequest_result"] = extracted_json
        # Save the conversation after updating process information
        self.history_manager._save_conversation(
            user_id, session_id, conversation)

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
                "status": "clarification_needed",
                "top_candidates": {}
            }

        # Check for subcategories to search
        if "subcategories" in extracted_json:
            subcategories = extracted_json.get("subcategories", [])
            self.logger.info(f"Identified subcategories: {subcategories}")

            # Get POI data for the subcategories
            poi_data = self.poi_manager.get_poi_by_subcategories(
                latitude, longitude, search_radius, subcategories)

            # Store POI process information
            last_message["processes"]["hidden"]["get_poi_by_subcategories_result"] = poi_data
            # Save the conversation after updating process information
            self.history_manager._save_conversation(
                user_id, session_id, conversation)

            if not poi_data:
                print("No POIs found for the identified subcategories")
                self.logger.warning(
                    "No POIs found for the identified subcategories")
                session["current_state"] = "new_query"
                self.state_manager.save_session(user_id, session_id, session)

                response_text = "I couldn't find any places matching your request. Could you try a different search term or a wider search radius?"
                self.history_manager.log_assistant_message(
                    user_id, session_id, response_text)

                return {
                    "response": response_text,
                    "status": "no_results",
                    "top_candidates": {}
                }

            # Find top candidates
            if self.num_candidates is None:
                # If num_candidates is not specified, use a default value of 4
                num_candidates = 4
            else:
                num_candidates = self.num_candidates

            top_candidates = self.top_candidates_finder.find_top_candidates(
                poi_data, latitude, longitude, search_radius, num_candidates)
            if not isinstance(top_candidates, dict):
                # If top_candidates is not a dict, create a dict with both drive and walk modes
                top_candidates = {
                    "drive": top_candidates, "walk": top_candidates}

            # Store top candidates in process information
            last_message["processes"]["hidden"]["top_candidates_result"] = top_candidates

            # Get advice based on the candidates
            advice_result = get_location_advice(
                user_input, formatted_history, top_candidates,
                latitude, longitude, search_radius)

            # Store advice process information
            last_message["processes"]["hidden"]["get_location_advice_result"] = advice_result

            # Update the response in the history
            self.history_manager.log_assistant_message(
                user_id, session_id, advice_result.get("response", ""),
                {
                    "status": "advice_provided",
                    "continuation": advice_result.get("continuation", False),
                    "top_candidate_result": top_candidates
                }
            )

            # Update session state
            if advice_result.get("continuation", False):
                session["current_state"] = "providing_advice"
                session["data"] = {
                    "prompt": user_input,
                    "top_candidates": top_candidates,
                    "extracted_json": extracted_json,
                    "latitude": latitude,
                    "longitude": longitude,
                    "search_radius": search_radius
                }
            else:
                session["current_state"] = "new_query"
            self.state_manager.save_session(user_id, session_id, session)

            return convert_nan_to_none({
                "response": advice_result.get("response", ""),
                "status": "advice_provided",
                "continuation": advice_result.get("continuation", False),
                "top_candidates": top_candidates
            })
        else:
            self.logger.warning("No subcategories found in LLM response")
            session["current_state"] = "new_query"
            self.state_manager.save_session(user_id, session_id, session)

            response_text = "I couldn't identify what you're looking for. Could you be more specific about the type of place you want to find?"
            self.history_manager.log_assistant_message(
                user_id, session_id, response_text)

            return convert_nan_to_none({
                "response": response_text,
                "status": "no_subcategories",
                "top_candidates": {}
            })

    def direct_location_search(self, user_id: str, session_id: str, search_prompt: str,
                               latitude: float, longitude: float, search_radius: int,
                               session: Dict[str, Any], formatted_history: str) -> Dict[str, Any]:
        """
        Directly perform location search without classification step.
        This handles the case where we've already identified a location to search near.

        Args:
            user_id: Unique identifier for the user
            session_id: Unique identifier for the current session
            search_prompt: Search prompt from the user
            latitude: User's current latitude
            longitude: User's current longitude
            search_radius: Search radius in meters for POIs
            session: Current session state
            formatted_history: Formatted conversation history

        Returns:
            Dict containing response and any additional action information
        """
        print("Direct candidates search Started:")
        self.logger.info(
            f"Directly searching for locations with coordinates: {latitude}, {longitude}")
        print(
            f"Directly searching for locations with coordinates: {latitude}, {longitude}")

        # Get the conversation to update process information
        conversation = self.history_manager._get_conversation(
            user_id, session_id)
        if not conversation["messages"]:
            return {"response": "Error: No message found", "status": "error"}

        last_message = conversation["messages"][-1]

        # First get categories and subcategories for context
        subcategories_for_context = self.poi_manager.get_available_categories(
            latitude, longitude, search_radius)
        print("Subcategories search for context:", subcategories_for_context)

        # Store process information
        last_message["processes"]["hidden"]["get_available_categories"] = subcategories_for_context
        # Save the conversation after updating process information
        self.history_manager._save_conversation(
            user_id, session_id, conversation)

        # Get subcategories from LLM
        extracted_json = llm_api(
            search_prompt, subcategories_for_context)
        subcategories = extracted_json.get("subcategories", [])
        print("Extracted JSON search:", subcategories)

        # Store LLM process information
        last_message["processes"]["hidden"]["llamarequest_result"] = extracted_json
        # Save the conversation after updating process information
        self.history_manager._save_conversation(
            user_id, session_id, conversation)

        # Get POI data for the identified subcategories
        candidates = self.poi_manager.get_poi_by_subcategories(
            latitude, longitude, search_radius, subcategories)

        # Store POI process information
        last_message["processes"]["hidden"]["get_poi_by_subcategories_result"] = candidates
        # Save the conversation after updating process information
        self.history_manager._save_conversation(
            user_id, session_id, conversation)

        if not candidates:
            print("No POIs found near specified location")
            self.logger.warning("No POIs found near specified location")
            session["current_state"] = "new_query"
            self.state_manager.save_session(user_id, session_id, session)

            response_text = "I couldn't find any places near that location. Could you try a different location or a wider search radius?"
            self.history_manager.log_assistant_message(
                user_id, session_id, response_text)

            return {
                "response": response_text,
                "status": "no_results",
                "top_candidates": {}
            }

        # Find top candidates
        if self.num_candidates is None:
            # If num_candidates is not specified, use a default value of 4
            num_candidates = 4
        else:
            num_candidates = self.num_candidates

        top_candidates = self.top_candidates_finder.find_top_candidates(
            candidates, latitude, longitude, search_radius, num_candidates)
        if not isinstance(top_candidates, dict):
            # If top_candidates is not a dict, create a dict with both drive and walk modes
            top_candidates = {"drive": top_candidates, "walk": top_candidates}

        # Get location advice for top candidates
        try:
            advice_result = get_location_advice(search_prompt, formatted_history, top_candidates,
                                                latitude, longitude, search_radius, True)

            # Check if we need to redirect to classification agent
            if "action" in advice_result and advice_result["action"] == "classification_agent":
                # Extract new search parameters
                print("Direct candidates search loop:")
                new_prompt = advice_result.get("prompt", search_prompt)
                new_latitude = advice_result.get("latitude", latitude)
                new_longitude = advice_result.get("longitude", longitude)
                new_radius = advice_result.get("radius", search_radius)

                # Update session state
                session["current_state"] = "new_query"
                session["data"] = {
                    "prompt": new_prompt,
                    "latitude": new_latitude,
                    "longitude": new_longitude,
                    "search_radius": new_radius
                }
                self.state_manager.save_session(user_id, session_id, session)

                # Directly search with new parameters without going through _process_query
                return self.direct_location_search(
                    user_id,
                    session_id,
                    new_prompt,
                    new_latitude,
                    new_longitude,
                    new_radius,
                    session,
                    formatted_history
                )

            # Standard response
            if "response" in advice_result:
                response_text = advice_result.get("response")
                continuation = str(advice_result.get(
                    "continuation", "false")).lower() == "true"

                # Log assistant response
                self.history_manager.log_assistant_message(
                    user_id, session_id, response_text)

                # Update session state
                session["current_state"] = "providing_advice"
                session["data"] = {
                    "prompt": search_prompt,
                    "top_candidates": top_candidates,
                    "latitude": latitude,
                    "longitude": longitude,
                    "search_radius": search_radius
                }
                self.state_manager.save_session(user_id, session_id, session)
                print("Direct candidates search ended:")
                return convert_nan_to_none({
                    "response": response_text,
                    "status": "advice_provided",
                    "continuation": continuation,
                    "top_candidates": top_candidates
                })
            else:
                self.logger.warning(
                    "Unexpected response format after direct location search")
                return convert_nan_to_none({
                    "response": "I found some places in that area, but I'm having trouble providing specific recommendations. Could you clarify what type of place you're looking for?",
                    "status": "error",
                    "top_candidates": {}
                })

        except Exception as e:
            self.logger.error(f"Direct location search error: {str(e)}")
            session["current_state"] = "new_query"
            self.state_manager.save_session(user_id, session_id, session)

            return convert_nan_to_none({
                "response": f"I encountered an error while searching for places: {str(e)}. Let's try again.",
                "status": "error",
                "top_candidates": {}
            })
