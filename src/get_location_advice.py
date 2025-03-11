from src.utils import timing_decorator
from config import LLAMA_API


@timing_decorator
def format_top_candidates(top_candidates):
    # print(top_candidates)

    lines = []
    for mode, candidates in top_candidates.items():
        lines.append(f"{mode.capitalize()} Mode:")
        if candidates:
            for poi in candidates:
                details = (
                    f"Name: {poi.get('name', 'N/A')}\n"
                    f"Description: {poi.get('description', 'N/A')}\n"
                    f"Location: {poi.get('location', 'N/A')}\n"
                    f"Tags: {poi.get('tags', 'N/A')}\n"
                    f"Latitude: {poi.get('coordinates.latitude', {})}\n"
                    f"Longitude: {poi.get('coordinates.longitude', {})}\n"
                    f"{mode.capitalize()} Route Distance: {poi.get(f'{mode}_route_distance_m', 'N/A'):.2f} meters"
                )
                lines.append(details)
        else:
            lines.append(
                f"No locations found within the specified route distance for {mode} mode.")
    return "\n\n".join(lines)


@timing_decorator
def get_location_advice(top_candidates, prompt):
    """
    Sends a request to the Llama API with the provided context information and user prompt.
    The system prompt instructs the AI to base its answer solely on the shared drive and walk mode data,
    and provide advice (e.g. suggesting taxi or walking) without revealing any extra data.
    """

    context_text = format_top_candidates(top_candidates)
    system_prompt = (
        "You are an AI assistant specialized in providing location suggestions. "
        "Based solely on the following information, analyze the user's request and provide a recommendation. "
        "Do not assume or add any information that is not given. "
        "Here is the available context:\n\n"
        f"{context_text}\n\n"
        "Please advise the user accordingly. For example, if no driving locations are available, suggest using a taxi, car, or walking if possible."
        "Give short answers, without any extra information. always give Name, Cordinate which is latitude and longitude, Distance, Tags"
        "Unless there is a single suggestion, give a list of suggestions in a sentence format"
    )

    api_request_json = {
        "model": "llama3.1-70b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User prompt: '{prompt}'"}
        ],
        "max_tokens": 200,
        "temperature": 0.2,
        "top_p": 0.9,
        "frequency_penalty": 0.8,
        "presence_penalty": 0.3,
        "stream": False
    }

    response = LLAMA_API.run(api_request_json)
    response_data = response.json()
    # Return the plain text answer provided by the API
    return response_data['choices'][0]['message']['content']
