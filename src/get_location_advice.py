from typing import List, Optional, Dict
import re
import json
import numpy as np
import uuid
from config import LLAMA_API
from src.utils import timing_decorator, extract_json_from_response

from src.data_types import TopCandidates, LocationAdviceResponse
from src.function_api_builder import build_location_request
from src.logger_setup import logger_instance


def format_top_candidates(top_candidates: TopCandidates) -> str:
    """
    Format top candidate points of interest into a readable string.
    Handles numpy types and None values properly.
    """
    logger = logger_instance.get_logger()
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

    logger.debug("Formatted top candidates: %s", "\n\n".join(lines))
    return "\n\n".join(lines) if lines else "No location data available."


@timing_decorator
def get_location_advice(prompt: str, history: List[str], top_candidates: TopCandidates,
                        latitude: float, longitude: float, search_radius: int,
                        conversation_id: Optional[str] = None) -> LocationAdviceResponse:
    logger = logger_instance.get_logger()
    """Main function to get location advice with structured response handling"""

    # Initialize conversation and history
    conversation_id = conversation_id or str(uuid.uuid4())
    logger.info("Started a new conversation with ID: %s", conversation_id)

    # Format context and history
    formatted_candidates = format_top_candidates(top_candidates)
    user_history = "\n".join(
        history) if history else "No previous conversation"

    logger.debug("Formatted user history: %s", user_history)
    logger.debug("Formatted candidates: %s", formatted_candidates)

    # Build API request
    api_request = build_location_request(
        prompt, formatted_candidates, user_history,
        latitude, longitude, search_radius
    )
    logger.debug(
        f"API request JSON from build_location_request: {api_request}")

    try:
        # Execute API call
        response = LLAMA_API.run(api_request)
        logger.info("API call executed successfully.")

        # Process response
        result = extract_json_from_response(response)

    except Exception as e:
        logger.error("API call failed: %s", e)
        result = LocationAdviceResponse(
            response="I couldn't process your request properly.",
            error=str(e)
        )

    logger.debug("API response processed with continuation: %s, response: %s",
                 result.get("continuation"), result.get("response"))

    return LocationAdviceResponse(
        continuation=result.get("continuation"),
        response=result.get("response")
    )
