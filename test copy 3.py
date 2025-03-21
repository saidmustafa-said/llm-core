from src.llamarequest import llm_api
from src.poi_filter import get_poi_data
from src.get_top_candidates import find_top_candidates
from src.get_location_advice import get_location_advice
import json
import os
import numpy as np


# Helper function to convert NumPy values to native Python types for JSON serialization
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
                print(f"Warning: Could not decode JSON from {history_file}")
                return {"conversation_id": conversation_id, "messages": [], "top_candidates": {}}
        return {"conversation_id": conversation_id, "messages": [], "top_candidates": {}}

    def save_history(self, conversation_id, user_prompt, response, top_candidates):
        history = self.load_history(conversation_id)
        history["messages"].append({"user": user_prompt, "response": response})

        # Convert top_candidates to native Python types before serialization
        if top_candidates:
            history["top_candidates"] = convert_numpy_to_native(top_candidates)
        else:
            # Ensure we're storing an empty dictionary, not an empty list
            history["top_candidates"] = {}

        history_file = self.get_history_file(conversation_id)
        try:
            with open(history_file, "w", encoding="utf-8") as file:
                json.dump(history, file, indent=4)
                print(f"DEBUG: Successfully saved history to {history_file}")
        except Exception as e:
            print(f"ERROR: Failed to save history: {e}")

    def get_conversation(self, conversation_id):
        history = self.load_history(conversation_id)
        return history.get("messages", [])

    def get_top_candidates(self, conversation_id):
        history = self.load_history(conversation_id)
        return history.get("top_candidates", {})

# Helper function to print a truncated version of large data


def print_truncated(data, max_length=50):
    if isinstance(data, (dict, list)):
        data_str = str(data)  # Convert to string
        print(data_str[:max_length] +
              ('...' if len(data_str) > max_length else ''))
    else:
        print(data)

# Main interaction loop


def main():
    history_manager = History()
    conversation_id = input("Enter conversation ID: ")

    latitude = 41.064108
    longitude = 29.031473
    search_radius = 2000
    num_candidates = 2

    while True:
        previous_messages = history_manager.get_conversation(conversation_id)
        stored_top_candidates = history_manager.get_top_candidates(
            conversation_id)
        top_candidates = {}  # Initialize as empty dictionary, not list

        print("\nDEBUG: Previous Messages:", previous_messages)
        print("DEBUG: Stored Top Candidates:")
        print_truncated(stored_top_candidates)  # Print truncated version

        # Check if stored_top_candidates is empty (using dictionary check)
        if not stored_top_candidates:
            user_prompt = input("Enter your prompt (or type 'exit' to quit): ")
            if user_prompt.lower() == 'exit':
                print("Exiting the conversation...")
                break

            user_context = [
                f"{msg['user']} {msg['response']}" for msg in previous_messages]
            print("DEBUG: User Context:", user_context)

            try:
                # First call to LLM API with context to get clarification or categories/tags
                print("DEBUG: Calling LLM API with user_prompt:", user_prompt)
                llm_response = llm_api(user_prompt, user_context)
                print("DEBUG: LLM Response:", llm_response)

                # Clarification handling loop
                while "clarification" in llm_response:
                    clarification_question = llm_response["clarification"]
                    print("Clarification Needed:", clarification_question)
                    additional_input = input("Provide clarification: ")
                    user_prompt += " " + additional_input
                    print("DEBUG: Updated User Prompt:", user_prompt)
                    llm_response = llm_api(user_prompt, user_context)
                    print("DEBUG: Updated LLM Response:", llm_response)

                # Once we have categories and tags, proceed with POI fetching
                search_categories = []
                search_tags = []

                if "categories" in llm_response:
                    search_categories = llm_response["categories"]
                    print("DEBUG: Search Categories:", search_categories)
                else:
                    print("Warning: No categories found in LLM response.")

                if "tags" in llm_response:
                    # Ensure we have a list of tags, even if empty
                    search_tags = llm_response["tags"] if llm_response["tags"] else [
                    ]
                    print("DEBUG: Search Tags:", search_tags)
                else:
                    print("Warning: No tags found in LLM response.")

                # Proceed only if we have valid categories
                if search_categories:
                    # Fetch POI candidates based on categories
                    candidates = get_poi_data(
                        latitude, longitude, search_radius, search_categories)
                    print("DEBUG: POI Candidates:")
                    print_truncated(candidates)  # Print truncated version

                    # If no POIs are found, inform the user and continue
                    if not candidates:
                        print("No POIs found based on your criteria.")
                        continue

                    # Filter and rank POIs based on relevance
                    candidate_results = find_top_candidates(
                        candidates, latitude, longitude, search_radius, num_candidates)
                    print("DEBUG: Top Candidates after filtering and ranking:")
                    # Print truncated version
                    print_truncated(candidate_results)

                    # Ensure top_candidates is a dictionary
                    top_candidates = {"default": candidate_results} if not isinstance(
                        candidate_results, dict) else candidate_results
                else:
                    print("Failed to extract valid categories from LLM response.")
                    continue

            except Exception as e:
                print(f"Error during API request or POI fetching: {e}")
                continue
        else:
            # Use stored candidates from previous interaction
            top_candidates = stored_top_candidates
            user_prompt = input("Enter your prompt (or type 'exit' to quit): ")
            if user_prompt.lower() == 'exit':
                print("Exiting the conversation...")
                break
            print("DEBUG: Using Stored Top Candidates:")
            print_truncated(top_candidates)  # Print truncated version

        # Get location advice based on top candidates
        try:
            location_advice = get_location_advice(
                top_candidates, user_prompt, previous_messages, latitude, longitude, search_radius)
            print("DEBUG: Location Advice Response:", location_advice)

            # Check if continuation is required
            # Parse string 'true'/'false' to boolean if needed
            if isinstance(location_advice.get("continuation", False), str):
                continuation = location_advice.get(
                    "continuation", "false").lower() == "true"
            else:
                continuation = location_advice.get("continuation", False)

            response_text = location_advice.get(
                "response", "No response received.")
            print("DEBUG: Continuation:", continuation)
            print("DEBUG: Response Text:", response_text)

            # Save conversation history with the top candidates
            # If continuation is True, keep the existing top_candidates
            history_manager.save_history(
                conversation_id,
                user_prompt,
                response_text,
                top_candidates if not continuation else stored_top_candidates
            )

            print("\nLocation Advice:", response_text)

            if continuation:
                print("Continuing conversation with stored context...")
            else:
                print("New search completed. Type 'exit' to end or ask a new question.")
        except Exception as e:
            print(f"Error during location advice processing: {e}")
            continue


if __name__ == "__main__":
    main()
