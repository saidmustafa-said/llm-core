# src/llamarequest.py
import os
import pandas as pd
from typing import List, Optional, Dict, Any
import json

from src.utils import timing_decorator
from src.data_types import LLMResponse
from src.function_api_builder import create_classification_request
from src.logger_setup import get_logger
from src.config.config import ConfigManager
from src.llm.llm_interface import LLMInterface


class LlamaRequest(LLMInterface):
    """
    Implementation of LLMInterface for the Llama API.
    """

    def __init__(self):
        """Initialize the LlamaRequest with configuration and cache."""
        self.config = ConfigManager()
        self.logger = get_logger()
        self.cache_manager = self.config.get_cache_manager()
        self.llama_api = self.config.get_llama_api()

    def extract_content(self, response: Dict[str, Any]) -> Any:
        """
        Extracts the JSON content from the response's 'content' field.

        Args:
            response: The raw API response

        Returns:
            The extracted content
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

    @timing_decorator
    def call_api(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Make a request to the Llama API with caching support.

        Args:
            prompt: The input prompt to send to the LLM
            **kwargs: Additional parameters for the API request

        Returns:
            LLMResponse: Structured response from the LLM
        """
        # Use the cached_call method to handle caching
        return self.cache_manager.cached_call(
            self._make_api_request, prompt, **kwargs
        )

    def _make_api_request(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Internal method to make the actual API request.
        This gets wrapped by the caching mechanism.

        Args:
            prompt: The input prompt to send to the LLM
            **kwargs: Additional parameters for the API request

        Returns:
            LLMResponse: Structured response from the LLM
        """
        self.logger.info("Calling LLM API with the provided prompt.")

        # Extract kwargs
        subcategories = kwargs.get('subcategories', [])

        existing_subcategories_str = subcategories
        self.logger.debug(
            f"Existing subcategories: {existing_subcategories_str}")

        # Prepare the API request
        api_request_json = create_classification_request(
            prompt, existing_subcategories_str)
        self.logger.debug(
            f"API request JSON from create_classification_request: {api_request_json}")

        # Call the LLAMA API
        try:
            response = self.llama_api.run(api_request_json)
            self.logger.info("Received response from LLAMA API.")
            self.logger.debug(f"Response: {response.json()}")
        except Exception as e:
            self.logger.error(f"Error calling LLAMA API: {e}")
            return LLMResponse({"error": f"Failed to call LLAMA API: {str(e)}"})

        # Extract and parse JSON from the response
        extracted_json = self.extract_content(response.json())

        return extracted_json


# Create a factory function to get an instance of the LLM interface
def get_llm_interface() -> LLMInterface:
    """
    Factory function to get the appropriate LLM interface implementation.

    Returns:
        LLMInterface: The configured LLM interface implementation
    """
    return LlamaRequest()


# For backward compatibility
@timing_decorator
def llm_api(prompt: str, subcategories) -> LLMResponse:
    """
    Legacy function for backward compatibility.

    Args:
        prompt: The input prompt to send to the LLM
        subcategories: Subcategories for classification

    Returns:
        LLMResponse: Structured response from the LLM
    """
    llm = get_llm_interface()
    return llm.call_api(prompt, subcategories=subcategories)
