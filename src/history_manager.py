import json
import os
import time
import uuid
from typing import Dict, List, Any, Optional


class HistoryManager:
    """
    Centralized history manager to store all conversation data in a single file.
    """

    def __init__(self, history_dir="chat_history"):
        self.history_dir = history_dir
        os.makedirs(self.history_dir, exist_ok=True)

    def get_history_file_path(self, conversation_id: str) -> str:
        """
        Get the path to the history file for a specific conversation.
        """
        return os.path.join(self.history_dir, f"{conversation_id}_history.json")

    def create_conversation(self) -> str:
        """
        Create a new conversation and return its ID.
        """
        conversation_id = str(uuid.uuid4())
        history_file = self.get_history_file_path(conversation_id)

        # Initialize history file with empty structure
        initial_data = {
            "conversation_id": conversation_id,
            "created_at": int(time.time()),
            "messages": []
        }

        with open(history_file, 'w') as f:
            json.dump(initial_data, f, indent=2)

        return conversation_id

    def get_conversation(self, conversation_id: str) -> Dict:
        """
        Get the full conversation history.
        """
        history_file = self.get_history_file_path(conversation_id)

        if not os.path.exists(history_file):
            # Create new conversation if doesn't exist
            return {
                "conversation_id": conversation_id,
                "created_at": int(time.time()),
                "messages": []
            }

        try:
            with open(history_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Handle corrupted files
            return {
                "conversation_id": conversation_id,
                "created_at": int(time.time()),
                "messages": []
            }

    def get_messages(self, conversation_id: str) -> List[Dict]:
        """
        Get just the messages part of the conversation history.
        """
        conversation = self.get_conversation(conversation_id)
        return conversation.get("messages", [])

    def get_formatted_history(self, conversation_id: str) -> List[str]:
        """
        Return history in a format suitable for context window.
        """
        messages = self.get_messages(conversation_id)
        formatted = []

        for msg in messages:
            if msg.get("role") == "user":
                formatted.append(f"User: {msg.get('content', '')}")
            elif msg.get("role") == "assistant":
                formatted.append(f"Assistant: {msg.get('content', '')}")

        return formatted

    def add_message(self, conversation_id: str, role: str, content: str,
                    metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a message to the conversation history.
        """
        history_file = self.get_history_file_path(conversation_id)
        conversation = self.get_conversation(conversation_id)

        message = {
            "role": role,
            "content": content,
            "timestamp": int(time.time())
        }

        if metadata:
            message["metadata"] = metadata

        conversation["messages"].append(message)

        with open(history_file, 'w') as f:
            json.dump(conversation, f, indent=2)

    def add_user_message(self, conversation_id: str, content: str,
                         metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a user message to history.
        """
        self.add_message(conversation_id, "user", content, metadata)

    def add_assistant_message(self, conversation_id: str, content: str,
                              metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add an assistant message to history.
        """
        self.add_message(conversation_id, "assistant", content, metadata)

    def add_llm_interaction(self, conversation_id: str,
                            prompt: str,
                            response: Dict,
                            request_data: Dict,
                            top_candidates: Optional[Dict] = None) -> None:
        """
        Add a full LLM interaction (both request and response) to history.
        """
        # Add user message first
        self.add_user_message(conversation_id, prompt)

        # Add assistant response with full metadata
        response_text = ""
        if isinstance(response, dict):
            response_text = response.get("response", str(response))
        else:
            response_text = str(response)

        metadata = {
            "full_request": request_data,
            "full_response": response,
            "timestamp": int(time.time())
        }

        if top_candidates:
            metadata["top_candidates"] = top_candidates

        self.add_assistant_message(conversation_id, response_text, metadata)

    def get_top_candidates(self, conversation_id: str) -> Dict:
        """
        Get the most recent top_candidates from the conversation history.
        """
        messages = self.get_messages(conversation_id)

        # Search backwards to find the most recent top_candidates
        for msg in reversed(messages):
            if msg.get("role") == "assistant" and msg.get("metadata"):
                if "top_candidates" in msg["metadata"]:
                    return msg["metadata"]["top_candidates"]

        return {}
