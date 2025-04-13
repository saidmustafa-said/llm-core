# managers/history/json_history_manager.py

import json
import os
import time
from typing import Dict, List, Any, Optional

from .history_manager import HistoryManager
from src.core.logger_setup import get_logger
from src.utils import convert_nan_to_none, serialize_for_json


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
            # Convert NaN values to None and prepare for JSON serialization
            serialized_conversation = serialize_for_json(conversation)

            with open(history_file, 'w') as f:
                json.dump(serialized_conversation, f, indent=2)
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

        # Create the new message structure
        message = {
            "prompt": {
                "visible": {
                    "type": event_type,
                    "content": content,
                    "timestamp": int(time.time())
                },
                "hidden": convert_nan_to_none(metadata) if metadata else {}
            },
            "processes": {
                "hidden": {}
            },
            "response": {
                "visible": {
                    "response": "",
                    "status": "pending",
                    "continuation": False
                },
                "hidden": {}
            }
        }

        conversation["messages"].append(message)
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
            prompt = msg["prompt"]["visible"]
            response = msg["response"]["visible"]

            # Add user message
            if prompt["type"] == "user_message":
                formatted_history.append(f"User: {prompt['content']}")

            # Add assistant response if it exists
            if response["response"]:
                formatted_history.append(f"Assistant: {response['response']}")

        return "\n".join(formatted_history)

    def log_user_message(self, user_id: str, session_id: str, content: str,
                         metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Log a user message to history."""
        # Prepare hidden metadata
        hidden_metadata = convert_nan_to_none(metadata) if metadata else {}

        # Ensure latitude, longitude, and search_radius are in the hidden fields
        if "latitude" in hidden_metadata and "longitude" in hidden_metadata:
            hidden_metadata["latitude"] = hidden_metadata.get("latitude")
            hidden_metadata["longitude"] = hidden_metadata.get("longitude")
            hidden_metadata["search_radius"] = hidden_metadata.get(
                "search_radius")
            hidden_metadata["num_candidates"] = hidden_metadata.get(
                "num_candidates")
        else:
            # If not provided, use null values
            hidden_metadata["latitude"] = None
            hidden_metadata["longitude"] = None
            hidden_metadata["search_radius"] = None
            hidden_metadata["num_candidates"] = None

        return self.log_event(user_id, session_id, "user_message", content, hidden_metadata)

    def log_assistant_message(self, user_id: str, session_id: str, content: str,
                              metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Log an assistant message to history."""
        # Get the last message to update its response
        conversation = self._get_conversation(user_id, session_id)
        if not conversation["messages"]:
            return False

        last_message = conversation["messages"][-1]
        last_message["response"]["visible"].update({
            "response": content,
            "status": metadata.get("status", "success") if metadata else "success",
            "continuation": metadata.get("continuation", False) if metadata else False
        })

        # Update hidden metadata
        if metadata:
            if "top_candidate_result" in metadata:
                last_message["response"]["hidden"]["top_candidate_result"] = convert_nan_to_none(
                    metadata["top_candidate_result"])

            # Update processes.hidden fields if they exist in metadata
            if "processes" in metadata and "hidden" in metadata["processes"]:
                last_message["processes"]["hidden"].update(
                    convert_nan_to_none(metadata["processes"]["hidden"]))

        return self._save_conversation(user_id, session_id, conversation)

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

    def save_conversation(self, user_id: str, session_id: str, conversation: Dict[str, Any]) -> bool:
        """
        Save a conversation to history.

        Args:
            user_id: The ID of the user
            session_id: The ID of the session/conversation
            conversation: The conversation data to save

        Returns:
            True if successful, False otherwise
        """
        # Convert NaN values to None before saving
        processed_conversation = convert_nan_to_none(conversation)
        return self._save_conversation(user_id, session_id, processed_conversation)
