from src.history_manager import History
from src.llamarequest import llm_api
from src.poi_filter import get_poi_data
from src.get_top_candidates import find_top_candidates
from src.get_location_advice import get_location_advice


def get_llm_response(user_prompt, user_context):
    llm_response = llm_api(user_prompt, user_context)
    print("DEBUG: LLM Response:", llm_response)

    # Check if clarification is needed
    clarification_needed = llm_response.get("clarification", None)

    if clarification_needed:
        # Clarification is a string, we can check if it's asking for clarification
        if isinstance(clarification_needed, str):
            print("Clarification Needed:", clarification_needed)
            additional_input = input("Provide clarification: ")
            user_prompt += " " + additional_input
            llm_response = llm_api(user_prompt, user_context)
        else:
            clarification_question = clarification_needed.get("question", "")
            if clarification_question:
                print("Clarification Needed:", clarification_question)
                additional_input = input("Provide clarification: ")
                user_prompt += " " + additional_input
                llm_response = llm_api(user_prompt, user_context)

    if 'error' in llm_response:
        print("Error:", llm_response['error'])
        return None

    return llm_response


def poi_process(llm_response, latitude, longitude, search_radius):
    search_categories = llm_response.get("categories", [])
    if not search_categories:
        print("Failed to extract valid categories from LLM response.")
        return []

    candidates = get_poi_data(
        latitude, longitude, search_radius, search_categories)
    if not candidates:
        print("No POIs found based on your criteria.")
    return candidates


def candidates_process(candidates, latitude, longitude, search_radius, num_candidates):
    candidate_results = find_top_candidates(
        candidates, latitude, longitude, search_radius, num_candidates)
    return {"default": candidate_results} if not isinstance(candidate_results, dict) else candidate_results


def get_location_advice_for_prompt(top_candidates, user_prompt, previous_messages, latitude, longitude, search_radius):
    try:
        print("DEBUG: Top Candidates before giving location advice:", top_candidates)

        location_advice = get_location_advice(
            user_prompt, previous_messages, top_candidates, latitude, longitude, search_radius)
        return location_advice
    except Exception as e:
        print(f"Error during location advice processing: {e}")
        return {}


def save_conversation_history(history_manager, conversation_id, user_prompt, response_text, top_candidates, continuation):
    try:
        history_manager.save_history(
            conversation_id,
            user_prompt,
            response_text,
            top_candidates if not continuation else top_candidates  # corrected this line
        )
    except Exception as e:
        print(f"Error saving history: {e}")


def main():
    history_manager = History()
    conversation_id = input("Enter conversation ID: ")

    previous_messages = history_manager.get_conversation(conversation_id)
    for msg in previous_messages:
        print(f"User: {msg['user']}")
        print(f"Bot: {msg['response']}")

    latitude = 41.064108
    longitude = 29.031473
    search_radius = 2000
    num_candidates = 2

    while True:
        stored_top_candidates = history_manager.get_top_candidates(
            conversation_id)
        top_candidates = {}

        if not stored_top_candidates:
            user_prompt = input("Enter your prompt (or type 'exit' to quit): ")
            if user_prompt.lower() == 'exit':
                break

            user_context = [
                f"{msg['user']} {msg['response']}" for msg in previous_messages]

            llm_response = get_llm_response(user_prompt, user_context)
            if llm_response is None:
                continue

            candidates = poi_process(
                llm_response, latitude, longitude, search_radius)
            if not candidates:
                continue

            top_candidates = candidates_process(
                candidates, latitude, longitude, search_radius, num_candidates)

        else:
            top_candidates = stored_top_candidates
            user_prompt = input("Enter your prompt (or type 'exit' to quit): ")
            if user_prompt.lower() == 'exit':
                break

        location_advice = get_location_advice_for_prompt(
            top_candidates, user_prompt, previous_messages, latitude, longitude, search_radius)
        response_text = location_advice.get(
            "response", "No response received.")
        print("\nLocation Advice:", response_text)

        continuation = location_advice.get("continuation", False)
        if isinstance(continuation, str):
            continuation = continuation.lower() == "true"

        save_conversation_history(history_manager, conversation_id,
                                  user_prompt, response_text, top_candidates, continuation)


if __name__ == "__main__":
    main()
