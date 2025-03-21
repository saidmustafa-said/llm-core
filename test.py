import os
from src.history_manager import HistoryManager
from src.llamarequest import llm_api
from src.poi_filter import get_poi_data  # Assumes you have this module
# Assumes you have this module
from src.get_top_candidates import find_top_candidates
# Assumes you have this module
from src.get_location_advice import get_location_advice
from src.data_types import LLMResponse, TopCandidates


def handle_clarification(llm_response: LLMResponse, prompt: str) -> str:
    clarification = llm_response.get("clarification")
    if clarification:
        if isinstance(clarification, str):
            additional_input = input(
                f"Clarification Needed: {clarification}\nProvide clarification: ")
        else:
            additional_input = input(
                f"Clarification Needed: {clarification.get('question', '')}\nProvide clarification: ")
        prompt = f"{prompt} {additional_input}"
    return prompt


def main():
    # Initialize shared history manager
    history_manager = HistoryManager()

    conversation_id_input = input(
        "Enter conversation ID (leave blank for new conversation): ")
    if conversation_id_input.strip():
        conversation_id = conversation_id_input.strip()
        if not os.path.exists(history_manager.get_history_file_path(conversation_id)):
            print(f"Creating new conversation with ID: {conversation_id}")
            history_manager.create_conversation(conversation_id)
    else:
        conversation_id = history_manager.create_conversation()
        print(f"Created new conversation with ID: {conversation_id}")

    messages = history_manager.get_messages(conversation_id)
    if messages:
        print("\n--- Conversation History ---")
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                print(f"User: {content}")
            elif role == "assistant":
                print(f"Bot: {content}")
        print("--- End of History ---\n")
    else:
        print("No previous messages in this conversation.")

    # Default location parameters
    latitude = 41.064108
    longitude = 29.031473
    search_radius = 5000
    num_candidates = 2

    while True:
        top_candidates: TopCandidates = history_manager.get_top_candidates(
            conversation_id)
        user_prompt = input("\nEnter your prompt (or type 'exit' to quit): ")
        if user_prompt.lower() == 'exit':
            break

        formatted_history = history_manager.get_formatted_history(
            conversation_id)

        if not top_candidates:
            # Get initial LLM classification response
            llm_response = llm_api(
                prompt=user_prompt,
                user_context=formatted_history,
                conversation_id=conversation_id,
                history_manager=history_manager
            )
            print(llm_response)
            print(llm_response.get(
                "categories", []))
            if llm_response is None or 'error' in llm_response:
                print("Error in LLM processing. Please try again.")
                continue

            # Handle any clarification request from the LLM
            user_prompt = handle_clarification(llm_response, user_prompt)
            llm_response = llm_api(
                prompt=user_prompt,
                user_context=formatted_history,
                conversation_id=conversation_id,
                history_manager=history_manager
            )
            print("LLM Response after clarification:", llm_response)
            print("LLM Response result:", llm_response.get(
                "categories", []))
            candidates = get_poi_data(
                latitude, longitude, search_radius, llm_response.get(
                    "categories", [])
            )
            if not candidates:
                print("No POIs found based on your criteria.")
                continue

            top_candidates = find_top_candidates(
                candidates, latitude, longitude, search_radius, num_candidates
            )
            if not isinstance(top_candidates, dict):
                top_candidates = {"default": top_candidates}

        # Get location advice based on the top candidates
        try:
            location_advice = get_location_advice(
                prompt=user_prompt,
                history=formatted_history,
                top_candidates=top_candidates,
                latitude=latitude,
                longitude=longitude,
                search_radius=search_radius,
                conversation_id=conversation_id,
                history_manager=history_manager
            )
        except Exception as e:
            print(f"Error during location advice processing: {e}")
            continue

        response_text = location_advice.get(
            "response", "No response received.")
        print("\nLocation Advice:", response_text)


if __name__ == "__main__":
    main()
