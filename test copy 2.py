# from src.llamarequest import llm_api
# from src.poi_filter import get_poi_data
# from src.get_top_candidates import find_top_candidates
# from src.get_location_advice import get_location_advice
# import json
# import os


# class History:
#     def __init__(self, history_dir="history"):
#         self.history_dir = history_dir
#         os.makedirs(self.history_dir, exist_ok=True)

#     def get_history_file(self, conversation_id):
#         return os.path.join(self.history_dir, f"{conversation_id}.json")

#     def load_history(self, conversation_id):
#         history_file = self.get_history_file(conversation_id)
#         if os.path.exists(history_file):
#             with open(history_file, "r", encoding="utf-8") as file:
#                 return json.load(file)
#         return {"conversation_id": conversation_id, "messages": []}

#     def save_history(self, conversation_id, user_prompt, response):
#         history = self.load_history(conversation_id)
#         history["messages"].append({"user": user_prompt, "response": response})

#         history_file = self.get_history_file(conversation_id)
#         with open(history_file, "w", encoding="utf-8") as file:
#             json.dump(history, file, indent=4)

#     def get_conversation(self, conversation_id):
#         history = self.load_history(conversation_id)
#         return history.get("messages", [])


# # Main interaction loop
# history_manager = History()

# conversation_id = input("Enter conversation ID: ")

# latitude = 41.064108
# longitude = 29.031473
# search_radius = 2000
# num_candidates = 2

# while True:
#     user_prompt = input("Enter your prompt (or type 'exit' to quit): ")

#     # Check if user wants to exit the conversation
#     if user_prompt.lower() == 'exit':
#         print("Exiting the conversation...")
#         break

#     # Get conversation history for context
#     previous_messages = history_manager.get_conversation(conversation_id)
#     user_context = [
#         f"{msg['user']} {msg['response']}" for msg in previous_messages]

#     # Call the LLM API to extract tags and categories
#     llm_response = llm_api(user_prompt, user_context)

#     if "clarification" in llm_response:
#         print("Clarification Needed:", llm_response["clarification"])
#         additional_input = input("Provide clarification: ")
#         user_prompt += " " + additional_input

#         # Re-run after clarification
#         llm_response = llm_api(user_prompt, user_context)

#     if "categories" in llm_response and "tags" in llm_response:
#         search_category = llm_response["categories"]
#         search_tag = llm_response["tags"]

#         # Step 2: Fetch candidate POIs (this should be your actual data fetching logic)
#         candidates = get_poi_data(
#             latitude, longitude, search_radius, search_category)
#         top_candidates = find_top_candidates(
#             candidates, latitude, longitude, search_radius, num_candidates)

#         # Step 3: Get location advice (another placeholder function)
#         location_advice = get_location_advice(
#             top_candidates, user_prompt, user_context, latitude, longitude, search_radius)

#         # Save conversation history
#         history_manager.save_history(
#             conversation_id, user_prompt, location_advice)

#         # Print results for debugging
#         print("Extracted Tags:", search_category)
#         print("Top Candidates:", top_candidates)
#         print("\n\n\nLocation Advice:", location_advice)

#     # Retrieve and print previous conversation history
#     previous_messages = history_manager.get_conversation(conversation_id)
#     print("\nPrevious Messages:", previous_messages)

# # End of script


from src.llamarequest import llm_api
from src.poi_filter import get_poi_data
from src.get_top_candidates import find_top_candidates
from src.get_location_advice import get_location_advice
import json
import os


class History:
    def __init__(self, history_dir="history"):
        self.history_dir = history_dir
        os.makedirs(self.history_dir, exist_ok=True)

    def get_history_file(self, conversation_id):
        return os.path.join(self.history_dir, f"{conversation_id}.json")

    def load_history(self, conversation_id):
        history_file = self.get_history_file(conversation_id)
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as file:
                return json.load(file)
        return {"conversation_id": conversation_id, "messages": [], "top_candidates": []}

    def save_history(self, conversation_id, user_prompt, response, top_candidates):
        history = self.load_history(conversation_id)
        history["messages"].append({"user": user_prompt, "response": response})
        history["top_candidates"] = top_candidates

        history_file = self.get_history_file(conversation_id)
        with open(history_file, "w", encoding="utf-8") as file:
            json.dump(history, file, indent=4)

    def get_conversation(self, conversation_id):
        history = self.load_history(conversation_id)
        return history.get("messages", [])

    def get_top_candidates(self, conversation_id):
        history = self.load_history(conversation_id)
        return history.get("top_candidates", [])


# Main interaction loop
history_manager = History()
conversation_id = input("Enter conversation ID: ")

latitude = 41.064108
longitude = 29.031473
search_radius = 2000
num_candidates = 2

while True:
    previous_messages = history_manager.get_conversation(conversation_id)
    stored_top_candidates = history_manager.get_top_candidates(conversation_id)
    top_candidates = []  # Ensure it is always initialized

    print("\nDEBUG: Previous Messages:", previous_messages)
    print("DEBUG: Stored Top Candidates:", stored_top_candidates)

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
            if "categories" in llm_response and "tags" in llm_response:
                search_category = llm_response["categories"]
                search_tag = llm_response["tags"]
                print("DEBUG: Search Category:", search_category)
                print("DEBUG: Search Tag:", search_tag)

                # Fetch POI candidates based on categories and tags
                candidates = get_poi_data(
                    latitude, longitude, search_radius, search_category)
                print("DEBUG: POI Candidates:", candidates)

                # If no POIs are found, inform the user and exit the loop
                if not candidates:
                    print("No POIs found based on your criteria.")
                    continue

                # Filter and rank POIs based on relevance
                top_candidates = find_top_candidates(
                    candidates, latitude, longitude, search_radius, num_candidates)
                print("DEBUG: Top Candidates after filtering and ranking:",
                      top_candidates)

                # Ensure top_candidates is a dictionary before storing
                top_candidates = {"default": top_candidates}
            else:
                print("Failed to extract categories and tags from LLM response.")
                continue

        except Exception as e:
            print(f"Error during API request or POI fetching: {e}")
            continue

    else:
        # Skip steps 1 and 2 if top_candidates exist, use stored ones
        top_candidates = stored_top_candidates if isinstance(
            stored_top_candidates, dict) else {"default": stored_top_candidates}
        print("DEBUG: Using Stored Top Candidates:", top_candidates)

    # Step 3: Get location advice based on top candidates
    try:
        location_advice = get_location_advice(
            top_candidates, user_prompt, previous_messages, latitude, longitude, search_radius)
        print("DEBUG: Location Advice Response:", location_advice)

        # Check if continuation is required
        continuation = location_advice.get("continuation", False)
        response_text = location_advice.get(
            "response", "No response received.")
        print("DEBUG: Continuation:", continuation)
        print("DEBUG: Response Text:", response_text)

        # Save conversation history with the top candidates (if not continuation)
        history_manager.save_history(conversation_id, user_prompt,
                                     response_text, top_candidates if not continuation else [])
        print("\nLocation Advice:", response_text)
        print("\nPrevious Messages:", previous_messages)

        if continuation:
            print("Continuing conversation with stored context...")
        else:
            print("Final advice given. Type 'exit' to end or ask a new question.")
    except Exception as e:
        print(f"Error during location advice processing: {e}")
        continue
