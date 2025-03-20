# from src.utils import timing_decorator
# from config import LLAMA_API


# @timing_decorator
# def format_top_candidates(top_candidates):
#     # print(top_candidates)

#     lines = []
#     for mode, candidates in top_candidates.items():
#         lines.append(f"{mode.capitalize()} Mode:")
#         if candidates:
#             for poi in candidates:
#                 details = (
#                     f"Name: {poi.get('name', 'N/A')}\n"
#                     f"Description: {poi.get('description', 'N/A')}\n"
#                     f"Location: {poi.get('location', 'N/A')}\n"
#                     f"Tags: {poi.get('tags', 'N/A')}\n"
#                     f"Latitude: {poi.get('coordinates.latitude', {})}\n"
#                     f"Longitude: {poi.get('coordinates.longitude', {})}\n"
#                     f"{mode.capitalize()} Route Distance: {poi.get(f'{mode}_route_distance_m', 'N/A'):.2f} meters"
#                 )
#                 lines.append(details)
#         else:
#             lines.append(
#                 f"No locations found within the specified route distance for {mode} mode.")
#     return "\n\n".join(lines)


# @timing_decorator
# def get_location_advice(top_candidates, prompt):
#     """
#     Sends a request to the Llama API with the provided context information and user prompt.
#     The system prompt instructs the AI to base its answer solely on the shared drive and walk mode data,
#     and provide advice (e.g. suggesting taxi or walking) without revealing any extra data.
#     """

#     print()
#     print()
#     print(context_text)
#     print()
#     print()

#     context_text = format_top_candidates(top_candidates)
#     system_prompt = (
#         "You are an AI assistant specialized in providing location suggestions. "
#         "Based solely on the given information, analyze the user's request and provide a recommendation. "
#         "Do not assume or add any information that is not given. "
#         "Here is the available context and dont use anything else if the context is empty, just reply to the user saying can you increase your search radius because i dont see anywhere close by:\n\n"
#         "Context START:"
#         f"{context_text}\n\n"
#         "Context END:"
#         "Please advise the user accordingly. For example, if no driving locations are available, suggest using a taxi, car, or walking if possible."
#         "Give short answers, without any extra information. always give Name, Cordinate which is latitude and longitude, Distance, Tags"
#         "Unless there is a single suggestion, give a list of suggestions in a sentence format"
#         "Make the conversation as you are a friend of the user and giving advice"
#         "Share the full address of the locations, name of place, open address, longitude and latitude"
#     )

#     api_request_json = {
#         "model": "llama3.1-70b",
#         "messages": [
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": f"User prompt: '{prompt}'"}
#         ],
#         "max_tokens": 300,
#         "temperature": 0.2,
#         "top_p": 0.9,
#         "frequency_penalty": 0.8,
#         "presence_penalty": 0.3,
#         "stream": False
#     }

#     response = LLAMA_API.run(api_request_json)
#     response_data = response.json()
#     # Return the plain text answer provided by the API
#     return response_data['choices'][0]['message']['content']


import numpy as np
from src.utils import timing_decorator
from config import LLAMA_API


@timing_decorator
def format_top_candidates(top_candidates):
    lines = []

    for mode, candidates in top_candidates.items():
        lines.append(f"{mode.capitalize()} Mode:")

        if candidates:
            for poi in candidates:
                details = [f"Mode: {mode.capitalize()}"]

                # Dynamically iterate through all the fields in the POI and append them to details
                for key, value in poi.items():
                    # Exclude NaN or None values
                    if value is None or (isinstance(value, float) and np.isnan(value)):
                        continue

                    # Handle nested fields like coordinates
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            # Exclude NaN or None values in nested dictionaries
                            if sub_value is None or (isinstance(sub_value, float) and np.isnan(sub_value)):
                                continue
                            details.append(
                                f"{sub_key.capitalize()}: {sub_value if sub_value is not None else 'N/A'}")
                    else:
                        details.append(
                            f"{key.capitalize()}: {value if value is not None else 'N/A'}")

                # Append the details to the final list
                lines.append("\n".join(details))
        else:
            lines.append(
                f"No locations found within the specified route distance for {mode} mode.")

    return "\n\n".join(lines)


@timing_decorator
def get_location_advice(top_candidates, prompt):
    """
    Sends a request to the Llama API with improved prompting for more conversational
    and helpful responses, even with limited information.
    """

    context_text = format_top_candidates(top_candidates)
    print()
    print()
    print(context_text)
    print()
    print()
    system_prompt = (
        "You are a friendly and helpful assistant who specializes in location recommendations. "
        "Think of yourself as a knowledgeable local friend who's helping someone navigate the area. "
        "Make recommendations based on the provided context data about nearby locations. "
        "\n\n"
        "Guidelines:"
        "\n- Be conversational and casual, like you're texting a friend"
        "\n- If the context contains location data, provide specific recommendations"
        "\n- If the context is empty or limited, acknowledge this but still be helpful by:"
        "\n  • Asking for more details about what they're looking for"
        "\n  • Suggesting they increase their search radius"
        "\n  • Offering general advice based on what you do know"
        "\n- For each recommendation, include key details when available: name, address, distance, and coordinates"
        "\n- Keep responses concise but informative"
        "\n- Consider transportation modes (walking, driving) in your suggestions"
        "\n- Match your tone to the user's query - be upbeat for entertainment queries, practical for necessities"
        "\n\n"
        "Context information:"
        "\n```\n"
        f"{context_text}\n"
        "```"
    )

    api_request_json = {
        "model": "llama3.1-70b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 350,
        "temperature": 0.7,  # Increased for more natural conversation
        "top_p": 0.95,
        "frequency_penalty": 0.5,
        "presence_penalty": 0.2,
        "stream": False
    }

    response = LLAMA_API.run(api_request_json)
    response_data = response.json()
    return response_data['choices'][0]['message']['content']
