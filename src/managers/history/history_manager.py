# managers/history/history_manager.py

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class HistoryManager(ABC):
    """
    Interface for conversation history management.
    Defines methods for logging events and retrieving conversation history.
    """

    @abstractmethod
    def log_event(self, user_id: str, session_id: str, event_type: str,
                  content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Log an event to the conversation history.
        
        Args:
            user_id: The ID of the user
            session_id: The ID of the session/conversation
            event_type: Type of event (e.g., 'user_message', 'assistant_message')
            content: The content of the event
            metadata: Optional additional data about the event
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_history(self, user_id: str, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve the conversation history for a session.
        
        Args:
            user_id: The ID of the user
            session_id: The ID of the session/conversation
            limit: Optional maximum number of events to return
            
        Returns:
            List of event dictionaries
        """
        pass

    @abstractmethod
    def get_formatted_history(self, user_id: str, session_id: str, limit: Optional[int] = None) -> str:
        """
        Get the conversation history formatted as a string.
        
        Args:
            user_id: The ID of the user
            session_id: The ID of the session/conversation
            limit: Optional maximum number of events to return
            
        Returns:
            Formatted history string
        """
        pass

    @abstractmethod
    def log_user_message(self, user_id: str, session_id: str, content: str,
                         metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Log a user message to history.
        
        Args:
            user_id: The ID of the user
            session_id: The ID of the session/conversation
            content: The message content
            metadata: Optional additional data
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def log_assistant_message(self, user_id: str, session_id: str, content: str,
                              metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Log an assistant message to history.
        
        Args:
            user_id: The ID of the user
            session_id: The ID of the session/conversation
            content: The message content
            metadata: Optional additional data
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def clear_history(self, user_id: str, session_id: str) -> bool:
        """
        Clear the history for a session.
        
        Args:
            user_id: The ID of the user
            session_id: The ID of the session/conversation
            
        Returns:
            True if successful, False otherwise
        """
        pass
