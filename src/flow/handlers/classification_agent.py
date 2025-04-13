from typing import Dict, Any


class ClassificationAgent:
    def _handle_classification(self, user_id: str, session_id: str, message: str) -> Dict[str, Any]:
        """Handle classification of user message."""
        # Get conversation history
        conversation = self.history_manager.get_conversation(
            user_id, session_id)

        # Prepare the message for classification
        classification_input = {
            "message": message,
            "history": conversation.get("messages", []),
            "metadata": {
                "user_id": user_id,
                "session_id": session_id
            }
        }

        # Get classification from LLM
        classification_result = self.llm.classify_message(classification_input)

        # Update conversation with classification results
        if "processes" not in conversation:
            conversation["processes"] = {"hidden": {}}

        # Update processes.hidden with classification results
        conversation["processes"]["hidden"].update({
            "classification": classification_result
        })

        # Save updated conversation
        self.history_manager.save_conversation(
            user_id, session_id, conversation)

        return classification_result

    def _handle_search(self, user_id: str, session_id: str, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle search request."""
        # Get conversation history
        conversation = self.history_manager.get_conversation(
            user_id, session_id)

        # Prepare search request
        search_request = {
            "query": search_params.get("query", ""),
            "filters": search_params.get("filters", {}),
            "num_candidates": search_params.get("num_candidates", 5),
            "metadata": {
                "user_id": user_id,
                "session_id": session_id
            }
        }

        # Perform search
        search_results = self.search_engine.search(search_request)

        # Update conversation with search results
        if "processes" not in conversation:
            conversation["processes"] = {"hidden": {}}

        # Update processes.hidden with search results
        conversation["processes"]["hidden"].update({
            "search_results": search_results
        })

        # Save updated conversation
        self.history_manager.save_conversation(
            user_id, session_id, conversation)

        return search_results
