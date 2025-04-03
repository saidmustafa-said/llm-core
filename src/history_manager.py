# history_manager.py
import json
import os
import time
import uuid
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class HistoryManager:
    """
    Centralized history manager to store conversation data by user and conversation.
    """

    def __init__(self, history_dir="chat_history"):
        self.history_dir = history_dir
        os.makedirs(self.history_dir, exist_ok=True)

    def get_user_folder_path(self, user_id: str) -> str:
        user_folder = os.path.join(self.history_dir, user_id)
        os.makedirs(user_folder, exist_ok=True)
        return user_folder

    def get_conversation_file_path(self, user_id: str, conversation_id: str) -> str:
        user_folder = self.get_user_folder_path(user_id)
        return os.path.join(user_folder, f"{conversation_id}.json")

    def create_conversation(self, user_id: str) -> str:
        """Generate a unique conversation ID and create a conversation file."""
        conversation_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"  # Unique ID: timestamp + short UUID

        conversation_file = self.get_conversation_file_path(
            user_id, conversation_id)

        initial_data = {
            "conversation_id": conversation_id,
            "created_at": int(time.time()),
            "messages": []
        }

        with open(conversation_file, 'w') as f:
            json.dump(initial_data, f, indent=2)

        logger.info(
            f"Created new conversation for user {user_id}: {conversation_id}")
        print(f"Created new conversation with ID: {conversation_id}")

        return conversation_id

    def get_conversation(self, user_id: str, conversation_id: str) -> Dict:
        conversation_file = self.get_conversation_file_path(
            user_id, conversation_id)

        if not os.path.exists(conversation_file):
            return {"conversation_id": conversation_id, "created_at": int(time.time()), "messages": []}

        try:
            with open(conversation_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error("JSON decode error in file: %s", conversation_file)
            return {"conversation_id": conversation_id, "created_at": int(time.time()), "messages": []}

    def get_messages(self, user_id: str, conversation_id: str) -> List[Dict]:
        conversation = self.get_conversation(user_id, conversation_id)
        return conversation.get("messages", [])

    def add_message(self, user_id: str, conversation_id: str, role: str, content: str,
                    metadata: Optional[Dict[str, Any]] = None) -> None:
        # Ensure content is a string
        if not isinstance(content, str):
            content = str(content)
        # Rest of the method remains the same
        conversation_file = self.get_conversation_file_path(
            user_id, conversation_id)
        conversation = self.get_conversation(user_id, conversation_id)

        message = {
            "role": role,
            "content": content,  # Now guaranteed to be a string
            "timestamp": int(time.time())
        }

        if metadata:
            message["metadata"] = metadata

        conversation["messages"].append(message)

        with open(conversation_file, 'w') as f:
            json.dump(conversation, f, indent=2)

    def add_user_message(self, user_id: str, conversation_id: str, content: str,
                         metadata: Optional[Dict[str, Any]] = None) -> None:
        self.add_message(user_id, conversation_id, "user", content, metadata)

    def add_assistant_message(self, user_id: str, conversation_id: str, content: str,
                              metadata: Optional[Dict[str, Any]] = None) -> None:
        self.add_message(user_id, conversation_id,
                         "assistant", content, metadata)

    def get_formatted_history(self, user_id: str, conversation_id: str) -> str:
        messages = self.get_messages(user_id, conversation_id)
        formatted_history = []
        for msg in messages:
            role = msg.get("role", "").capitalize()
            content = msg.get("content", "")
            # Handle cases where content might be a list (due to data issues)
            if isinstance(content, list):
                content = " ".join(content)
            formatted_history.append(f"{role}: {content}")
        return "\n".join(formatted_history)

    def add_llm_interaction(self, user_id: str, conversation_id: str,
                            response: Any, request_data: Dict,
                            top_candidates: Optional[Dict] = None) -> None:
        response_text = str(response) if isinstance(
            response, dict) else response.get("response", "")
        metadata = {
            "request_type": request_data.get("request_type", "unknown"),
            "timestamp": request_data.get("timestamp", int(time.time())),
            "tokens": request_data.get("token_counts", {})
        }
        if top_candidates:
            metadata["top_candidates"] = top_candidates
        self.add_assistant_message(
            user_id, conversation_id, response_text, metadata)
