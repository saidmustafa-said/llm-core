import json
import os
import numpy as np


def convert_numpy_to_native(obj):
    if isinstance(obj, dict):
        return {k: convert_numpy_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_native(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return convert_numpy_to_native(obj.tolist())
    else:
        return obj


class History:
    def __init__(self, history_dir="history"):
        self.history_dir = history_dir
        os.makedirs(self.history_dir, exist_ok=True)

    def get_history_file(self, conversation_id):
        return os.path.join(self.history_dir, f"{conversation_id}.json")

    def load_history(self, conversation_id):
        history_file = self.get_history_file(conversation_id)
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as file:
                    return json.load(file)
            except json.JSONDecodeError:
                return {"conversation_id": conversation_id, "messages": [], "top_candidates": {}}
        return {"conversation_id": conversation_id, "messages": [], "top_candidates": {}}

    def save_history(self, conversation_id, user_prompt, response, top_candidates):
        history = self.load_history(conversation_id)
        history["messages"].append({"user": user_prompt, "response": response})

        if top_candidates:
            history["top_candidates"] = convert_numpy_to_native(top_candidates)
        else:
            history["top_candidates"] = {}

        history_file = self.get_history_file(conversation_id)
        try:
            with open(history_file, "w", encoding="utf-8") as file:
                json.dump(history, file, indent=4)
        except Exception:
            pass

    def get_conversation(self, conversation_id):
        history = self.load_history(conversation_id)
        return history.get("messages", [])

    def get_top_candidates(self, conversation_id):
        history = self.load_history(conversation_id)
        return history.get("top_candidates", {})
