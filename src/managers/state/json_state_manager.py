# managers/state/json_state_manager.py

import json
import os
import time
import uuid
from typing import Dict, Any, Optional

from .state_manager import StateManager
from src.core.logger_setup import get_logger


class JSONStateManager(StateManager):
    """
    JSON file-based implementation of the StateManager interface.
    Stores session states in a JSON file.
    """

    def __init__(self, sessions_dir="sessions"):
        """
        Initialize JSONStateManager with the directory to store session files.

        Args:
            sessions_dir: Directory to store session files
        """
        self.sessions_dir = sessions_dir
        os.makedirs(self.sessions_dir, exist_ok=True)
        self.logger = get_logger()

    def _get_user_folder_path(self, user_id: str) -> str:
        """Get the folder path for a user and create if not exists."""
        user_folder = os.path.join(self.sessions_dir, user_id)
        os.makedirs(user_folder, exist_ok=True)
        return user_folder

    def _get_session_file_path(self, user_id: str, session_id: str) -> str:
        """Get the file path for a user's session."""
        user_folder = self._get_user_folder_path(user_id)
        return os.path.join(user_folder, f"{session_id}.json")

    def get_session(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a session state from the JSON file."""
        session_file = self._get_session_file_path(user_id, session_id)

        if not os.path.exists(session_file):
            self.logger.warning(f"Session file not found: {session_file}")
            return None

        try:
            with open(session_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            self.logger.error(
                f"JSON decode error in session file: {session_file}")
            return None

    def save_session(self, user_id: str, session_id: str, state: Dict[str, Any]) -> bool:
        """Save a session state to the JSON file."""
        session_file = self._get_session_file_path(user_id, session_id)

        try:
            with open(session_file, 'w') as f:
                json.dump(state, f, indent=2)
            self.logger.debug(
                f"Session saved: {session_id} for user {user_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving session {session_id}: {str(e)}")
            return False

    def delete_session(self, user_id: str, session_id: str) -> bool:
        """Rename the session file with REMOVED prefix instead of deleting"""
        session_file = self._get_session_file_path(user_id, session_id)

        if not os.path.exists(session_file):
            self.logger.warning(
                f"Cannot delete non-existent session: {session_id}")
            return False

        try:
            dir_path = os.path.dirname(session_file)
            file_name = os.path.basename(session_file)
            new_path = os.path.join(dir_path, f"REMOVED_{file_name}")
            os.rename(session_file, new_path)
            self.logger.info(
                f"Marked session as removed: {new_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting session {session_id}: {str(e)}")
            return False

    def create_session(self, user_id: str) -> str:
        """Create a new session for a user."""
        session_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"  # Unique ID: timestamp + short UUID

        initial_state = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": int(time.time()),
            "current_state": "initial",
            "data": {}
        }

        success = self.save_session(user_id, session_id, initial_state)

        if success:
            self.logger.info(
                f"Created new session for user {user_id}: {session_id}")
            return session_id
        else:
            self.logger.error(
                f"Failed to create new session for user {user_id}")
            return ""
