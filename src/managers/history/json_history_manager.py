# managers/history/json_history_manager.py

import json
import os
import time
from typing import Dict, List, Any, Optional

from .history_manager import HistoryManager
from src.logger_setup import get_logger


class JSONHistoryManager(HistoryManager):
    """
    JSON file-based implementation of the HistoryManager interface.
    Stores conversation history in JSON files.
    """

    def __init__(self, history_dir="chat_history"):
        """
        Initialize JSONHistoryManager with the directory to store history files.

        Args:
            history_dir: Directory to store history files
        """
        self.history_dir = history_dir
        os.makedirs(self.history_dir, exist_ok=True)
        self.logger = get_logger()

    def _get_user_folder_path(self, user_id: str) -> str:
        """Get the folder path for a user and create if not exists."""
        user_folder = os.path.join(self.history_dir, user_id)
        os.makedirs(user_folder, exist_ok=True)
        return user_folder

    def _get_history_file_path(self, user_id: str, session_id: str) -> str:
        """Get the file path for a user's conversation history."""
        user_folder = self._get_user_folder_path(user_id)
        return os.path.join(user_folder, f"{session_id}.json")

    def _get_conversation(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Get the conversation data or create a new one if it doesn't exist."""
        history_file = self._get_history_file_path(user_id, session_id)

        if not os.path.exists(history_file):
            return {
                "session_id": session_id,
                "created_at": int(time.time()),
                "messages": []
            }

        try:
            with open(history_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            self.logger.error(
                f"JSON decode error in history file: {history_file}")
            return {
                "session_id": session_id,
                "created_at": int(time.time()),
                "messages": []
            }

    def _save_conversation(self, user_id: str, session_id: str, conversation: Dict[str, Any]) -> bool:
        """Save the conversation data to the file."""
        history_file = self._get_history_file_path(user_id, session_id)

        try:
            with open(history_file, 'w') as f:
                json.dump(conversation, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(
                f"Error saving conversation {session_id}: {str(e)}")
            return False

    def log_event(self, user_id: str, session_id: str, event_type: str,
                  content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Log an event to the conversation history."""
        # Ensure content is a string
        if not isinstance(content, str):
            content = str(content)

        conversation = self._get_conversation(user_id, session_id)

        event = {
            "type": event_type,
            "content": content,
            "timestamp": int(time.time())
        }

        if metadata:
            event["metadata"] = metadata

        conversation["messages"].append(event)

        return self._save_conversation(user_id, session_id, conversation)

    def get_history(self, user_id: str, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve the conversation history for a session."""
        conversation = self._get_conversation(user_id, session_id)
        messages = conversation.get("messages", [])

        if limit is not None and limit > 0:
            messages = messages[-limit:]

        return messages

    def get_formatted_history(self, user_id: str, session_id: str, limit: Optional[int] = None) -> str:
        """Get the conversation history formatted as a string."""
        messages = self.get_history(user_id, session_id, limit)
        formatted_history = []

        for msg in messages:
            event_type = msg.get("type", "unknown")
            content = msg.get("content", "")

            # Determine the role based on event type
            if event_type == "user_message":
                role = "User"
            elif event_type == "assistant_message":
                role = "Assistant"
            else:
                role = event_type.capitalize()

            # Handle cases where content might be a list (due to data issues)
            if isinstance(content, list):
                content = " ".join(content)

            formatted_history.append(f"{role}: {content}")

        return "\n".join(formatted_history)

    def log_user_message(self, user_id: str, session_id: str, content: str,
                         metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Log a user message to history."""
        return self.log_event(user_id, session_id, "user_message", content, metadata)

    def log_assistant_message(self, user_id: str, session_id: str, content: str,
                              metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Log an assistant message to history."""
        return self.log_event(user_id, session_id, "assistant_message", content, metadata)

    def clear_history(self, user_id: str, session_id: str) -> bool:
        """Clear the history for a session."""
        conversation = self._get_conversation(user_id, session_id)
        conversation["messages"] = []
        return self._save_conversation(user_id, session_id, conversation)

    def delete_history(self, user_id: str, session_id: str) -> None:
        """Rename the history file with REMOVED prefix instead of deleting"""
        file_path = self._get_history_file_path(user_id, session_id)
        if os.path.exists(file_path):
            dir_path = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            new_path = os.path.join(dir_path, f"REMOVED_{file_name}")
            os.rename(file_path, new_path)
            self.logger.info(f"Marked history as removed: {new_path}")
