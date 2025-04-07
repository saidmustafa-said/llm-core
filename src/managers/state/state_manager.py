# managers/state/state_manager.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class StateManager(ABC):
    """
    Interface for session state management.
    Defines methods for getting, saving, and deleting user session states.
    """

    @abstractmethod
    def get_session(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a session state by user_id and session_id.
        
        Args:
            user_id: The ID of the user
            session_id: The ID of the session
            
        Returns:
            Session state dictionary or None if not found
        """
        pass

    @abstractmethod
    def save_session(self, user_id: str, session_id: str, state: Dict[str, Any]) -> bool:
        """
        Save a session state for a user.
        
        Args:
            user_id: The ID of the user
            session_id: The ID of the session
            state: The state dictionary to save
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def delete_session(self, user_id: str, session_id: str) -> bool:
        """
        Delete a session state.
        
        Args:
            user_id: The ID of the user
            session_id: The ID of the session
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def create_session(self, user_id: str) -> str:
        """
        Create a new session for a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            The new session ID
        """
        pass
