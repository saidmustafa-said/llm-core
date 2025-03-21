import json
import os
import time
import uuid
import logging
from typing import Dict, List, Any, Optional
from src.data_types import Message, Conversation, TopCandidates, LLMResponse


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class HistoryManager:
    """
    Centralized history manager to store all conversation data in a single file.
    """

    def __init__(self, history_dir="chat_history"):
        self.history_dir = history_dir
        os.makedirs(self.history_dir, exist_ok=True)

    def get_history_file_path(self, conversation_id: str) -> str:
        return os.path.join(self.history_dir, f"{conversation_id}_history.json")

    def _default_conversation(self, conversation_id: str) -> Conversation:
        return {
            "conversation_id": conversation_id,
            "created_at": int(time.time()),
            "messages": []
        }

    def create_conversation(self, conversation_id: str) -> Conversation:
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
        history_file = self.get_history_file_path(conversation_id)
        initial_data = self._default_conversation(conversation_id)
        with open(history_file, 'w') as f:
            json.dump(initial_data, f, indent=2)
        return conversation_id

    def get_conversation(self, conversation_id: str) -> Dict:
        history_file = self.get_history_file_path(conversation_id)
        if not os.path.exists(history_file):
            return self._default_conversation(conversation_id)
        try:
            with open(history_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error("JSON decode error in file: %s", history_file)
            return self._default_conversation(conversation_id)

    def get_messages(self, conversation_id: str) -> List[Dict]:
        conversation = self.get_conversation(conversation_id)
        return conversation.get("messages", [])

    def get_formatted_history(self, conversation_id: str) -> List[str]:
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
        self.add_message(conversation_id, "user", content, metadata)

    def add_assistant_message(self, conversation_id: str, content: str,
                              metadata: Optional[Dict[str, Any]] = None) -> None:
        self.add_message(conversation_id, "assistant", content, metadata)

    def add_llm_interaction(self, conversation_id: str,
                           prompt: str,
                           response: LLMResponse,
                           request_data: Dict,
                           top_candidates: Optional[TopCandidates] = None) -> None:
        # Add user prompt and assistant response with full metadata to history.
        self.add_user_message(conversation_id, prompt)
        response_text = response.get("response", str(response)) if isinstance(
            response, dict) else str(response)
        metadata = {
            "full_request": request_data,
            "full_response": response,
            "timestamp": int(time.time())
        }
        if top_candidates:
            metadata["top_candidates"] = top_candidates
        self.add_assistant_message(conversation_id, response_text, metadata)

    def get_top_candidates(self, conversation_id: str) -> TopCandidates:
        messages = self.get_messages(conversation_id)
        # Search backwards for the most recent top_candidates
        for msg in reversed(messages):
            if msg.get("role") == "assistant" and msg.get("metadata"):
                if "top_candidates" in msg["metadata"]:
                    return msg["metadata"]["top_candidates"]
        return TopCandidates({})
