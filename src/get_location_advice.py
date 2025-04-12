# src/get_location_advice.py

from typing import List, Optional, Dict
import re
import json
import numpy as np
import uuid

from src.utils import timing_decorator
from src.data_types import TopCandidates, LocationAdviceResponse
from src.function_api_builder import build_location_request, build_location_request_search
from src.logger_setup import get_logger
from src.config_manager import ConfigManager
from src.llm.llm_interface import LLMInterface


class LocationAdviceRequest(LLMInterface):
    """
    Implementation of LLMInterface for location advice requests.
    """

    def __init__(self):
        """Initialize with configuration and cache."""
        self.config = ConfigManager()
        self.logger = get_logger()
        self.cache_manager = self.config.get_cache_manager()
        self.llama_api = self.config.get_llama_api()

    def extract_content(self, response):
        """
        Extracts the JSON content from the response's 'content' field.
        """
        try:
            # Navigate to the content field
            content_str = response.get("choices", [{}])[0].get(
                "message", {}).get("content", "")

            # Parse the JSON
            extracted_json = json.loads(content_str)

            return extracted_json
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            self.logger.error(f"Error extracting content: {e}")
            return None

    def format_top_candidates(self, top_candidates: TopCandidates) -> str:
        """
        Format top candidate points of interest into a readable string.
        Handles numpy types and None values properly.
        """
        lines = []

        for mode, candidates in top_candidates.items():
            lines.append(f"{mode.capitalize()} Mode:")

            if candidates and len(candidates) > 0:
                for poi in candidates:
                    details = [f"Mode: {mode.capitalize()}"]

                    for key, value in poi.items():
                        # Convert numpy types to Python native types
                        if isinstance(value, np.generic):
                            value = value.item()  # Replaced np.asscalar with .item()

                        if value is None or (isinstance(value, float) and np.isnan(value)):
                            continue

                        if isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                if isinstance(sub_value, np.generic):
                                    sub_value = sub_value.item()  # Replaced np.asscalar with .item()
                                if sub_value is None or (isinstance(sub_value, float) and np.isnan(sub_value)):
                                    continue
                                details.append(
                                    f"{sub_key.capitalize()}: {sub_value}")
                        else:
                            details.append(f"{key.capitalize()}: {value}")

                    lines.append("\n".join(details))
            else:
                lines.append(
                    f"No locations found within the specified route distance for {mode} mode.")

        self.logger.debug("Formatted top candidates: %s", "\n\n".join(lines))
        return "\n\n".join(lines) if lines else "No location data available."

    @timing_decorator
    def call_api(self, prompt: str, **kwargs) -> LocationAdviceResponse:
        """
        Make a request to the LLM API for location advice with caching support.

        Args:
            prompt: The input prompt to send to the LLM
            **kwargs: Additional parameters for the API request

        Returns:
            LocationAdviceResponse: Structured response with location advice
        """
        # Use the cached_call method to handle caching
        return self.cache_manager.cached_call(
            self._make_api_request, prompt, **kwargs
        )

    def _make_api_request(self, prompt: str, **kwargs) -> LocationAdviceResponse:
        """
        Internal method to make the actual API request.
        This gets wrapped by the caching mechanism.
        """
        # Extract kwargs
        history = kwargs.get('history', None)
        top_candidates = kwargs.get('top_candidates', {})
        latitude = kwargs.get('latitude', 0.0)
        longitude = kwargs.get('longitude', 0.0)
        search_radius = kwargs.get('search_radius', 1000)
        flag = kwargs.get('flag', False)

        # Format context and history
        formatted_candidates = self.format_top_candidates(top_candidates)

        # Handle history - now expecting pre-formatted string
        user_history = history if history else "No previous conversation"

        self.logger.debug("User history: %s",
                          user_history.replace('\n', ' || '))
        self.logger.debug("Formatted candidates: %s", formatted_candidates)

        if flag:
            # Build API request for search
            api_request = build_location_request_search(
                prompt, formatted_candidates, user_history,
                latitude, longitude, search_radius
            )
        else:
            # Build API request
            api_request = build_location_request(
                prompt, formatted_candidates, user_history,
                latitude, longitude, search_radius
            )
        self.logger.debug(
            f"API request JSON from build_location_request: {api_request}")

        try:
            # Execute API call
            response = self.llama_api.run(api_request)
            self.logger.info("Received response from LLAMA API.")
            self.logger.debug(f"Response: {response.json()}")

            # Process response
            extracted_json = self.extract_content(response.json())
            return extracted_json

        except Exception as e:
            self.logger.error("Location Advice API failed: %s", e)
            return {"error": str(e)}


# Create a factory function to get an instance of the location advice interface
def get_location_advice_interface() -> LLMInterface:
    """
    Factory function to get the location advice interface implementation.

    Returns:
        LLMInterface: The configured location advice interface
    """
    return LocationAdviceRequest()


# For backward compatibility
@timing_decorator
def get_location_advice(prompt, history, top_candidates: TopCandidates,
                        latitude, longitude, search_radius, flag=False) -> LocationAdviceResponse:
    """
    Legacy function for backward compatibility.

    Args:
        prompt: The input prompt to send to the LLM
        history: Previous conversation history
        top_candidates: Candidate locations 
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        search_radius: Search radius in meters
        flag: Whether to use search mode

    Returns:
        LocationAdviceResponse: Structured response with location advice
    """
    location_advice = get_location_advice_interface()
    return location_advice.call_api(
        prompt,
        history=history,
        top_candidates=top_candidates,
        latitude=latitude,
        longitude=longitude,
        search_radius=search_radius,
        flag=flag
    )
