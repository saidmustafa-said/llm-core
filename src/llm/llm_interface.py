# src/llm/llm_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from src.core.data_types import LLMResponse


class LLMInterface(ABC):
    """
    Abstract interface for LLM API calls.
    This interface allows for different LLM providers to be used interchangeably.
    """

    @abstractmethod
    def call_api(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Make a request to the LLM API.

        Args:
            prompt: The input prompt to send to the LLM
            **kwargs: Additional parameters specific to the implementation

        Returns:
            LLMResponse: Structured response from the LLM
        """
        pass

    @abstractmethod
    def extract_content(self, response: Dict[str, Any]) -> Any:
        """
        Extract the relevant content from the API response.

        Args:
            response: The raw API response

        Returns:
            The extracted content
        """
        pass
