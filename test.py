import os
from src.history_manager import HistoryManager
from src.llamarequest import llm_api
from src.poi_filter import get_poi_data
from src.get_top_candidates import find_top_candidates
from src.get_location_advice import get_location_advice
from src.data_types import LLMResponse, TopCandidates


def handle_clarification(llm_response: LLMResponse, prompt: str, formatted_history: str, conversation_id: str, history_manager: HistoryManager) -> str:
    clarification = llm_response.get("clarification")
    if clarification:
        if isinstance(clarification, str):
            additional_input = input(
                f"Clarification Needed: {clarification}\nProvide clarification: ")
        else:
            additional_input = input(
                f"Clarification Needed: {clarification.get('question', '')}\nProvide clarification: ")

        # Append user input to the prompt
        prompt = f"{prompt} {additional_input}"

        # Re-run the llm_api call to get updated LLM response after clarification
        llm_response = llm_api(
            prompt=prompt,
            user_context=formatted_history,
            conversation_id=conversation_id,
            history_manager=history_manager
        )

        print("LLM Response after clarification:", llm_response)
        print("LLM Response result:", llm_response.get("categories", []))

        # Check for errors in the LLM response after clarification
        if llm_response is None or 'error' in llm_response:
            print("Error in LLM processing. Please try again.")
            return prompt  # Return the original prompt if an error occurs

        # Check if we need further clarification
        if llm_response.get("clarification"):
            # Recursive call to handle additional clarification
            return handle_clarification(llm_response, prompt, formatted_history, conversation_id, history_manager)

    return prompt


def process_new_query(user_prompt: str, formatted_history: str, conversation_id: str,
                      history_manager: HistoryManager, latitude: float, longitude: float,
                      search_radius: int, num_candidates: int) -> TopCandidates:
    """Process a new user query to get new top candidates."""
    # Get initial LLM classification response
    llm_response = llm_api(
        prompt=user_prompt,
        user_context=formatted_history,
        conversation_id=conversation_id,
        history_manager=history_manager
    )

    print(llm_response)
    print(llm_response.get("categories", []))

    if llm_response is None or 'error' in llm_response:
        print("Error in LLM processing. Please try again.")
        return None

    # Handle any clarification request from the LLM
    user_prompt = handle_clarification(
        llm_response, user_prompt, formatted_history, conversation_id, history_manager)

    if not user_prompt:
        return None  # If there's an error, return None

    categories = llm_response.get("categories", [])
    print(f"Categories to search for: {categories}")

    candidates = get_poi_data(
        latitude, longitude, search_radius, categories
    )

    if not candidates:
        print("No POIs found based on your criteria.")
        return None

    top_candidates = find_top_candidates(
        candidates, latitude, longitude, search_radius, num_candidates
    )

    if not isinstance(top_candidates, dict):
        top_candidates = {"default": top_candidates}

    return top_candidates


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

    top_candidates = None
    reuse_prompt = False
    last_prompt = ""

    while True:
        if not reuse_prompt:
            user_prompt = input(
                "\nEnter your prompt (or type 'exit' to quit): ")
            if user_prompt.lower() == 'exit':
                break
            last_prompt = user_prompt
        else:
            user_prompt = last_prompt
            reuse_prompt = False
            print(f"\nReusing last prompt: {user_prompt}")

        formatted_history = history_manager.get_formatted_history(
            conversation_id)

        # If we don't have top candidates yet, process a new query
        if not top_candidates:
            top_candidates = process_new_query(
                user_prompt, formatted_history, conversation_id,
                history_manager, latitude, longitude, search_radius, num_candidates
            )
            if not top_candidates:
                continue  # Skip to next loop iteration if processing failed

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
        print("Continuation:", location_advice)
        continuation = location_advice.get("continuation", "false")

        while continuation.lower() == "true":
            user_prompt = input(
                "\nEnter your prompt (or type 'exit' to quit): ")
            if user_prompt.lower() == 'exit':
                break
            last_prompt = user_prompt  # Update the last prompt

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

            continuation = location_advice.get("continuation", "false")
            response_text = location_advice.get(
                "response", "No response received.")

            if continuation.lower() == "false":
                break
            else:
                print("\nLocation Advice:", response_text)

        if continuation.lower() == "false":
            # If continuation is false, clear top_candidates to get new ones on next iteration
            print("Starting new recommendation context with the same prompt.")
            top_candidates = None
            reuse_prompt = True  # Flag to reuse the last prompt
            # Continue to restart the loop with the same prompt
