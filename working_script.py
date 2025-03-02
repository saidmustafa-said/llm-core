
import math
import networkx as nx
import osmnx as ox
import json
import re
import os
import pandas as pd
from llamaapi import LlamaAPI

# Initialize the LlamaAPI SDK
llama = LlamaAPI("2048ca26-30cc-4c2e-ad95-fe45e7e1b482")


def retrieve_tags():
    """
    Retrieves tags from the CSV file (tags.csv) and returns them as a formatted string.
    """
    tags_file = os.path.join("great_data", "tags.csv")

    if not os.path.exists(tags_file):
        return "None"

    tags_df = pd.read_csv(tags_file)

    if 'tags' in tags_df.columns:
        tags_list = tags_df['tags'].dropna().tolist()
        return ", ".join(tags_list) if tags_list else "None"
    else:
        return "None"


def llm_api(prompt):
    """
    Interacts with the Llama API to send a prompt and retrieve tags based on the user's input.
    """
    existing_tags_str = retrieve_tags()

    api_request_json = {
        "model": "llama3.1-70b",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an AI specialized in location tagging. "
                    f"Here are the existing tags: {existing_tags_str}. "
                    "Your task is to analyze the user's prompt and see if any of the existing tags match. "
                    "If they don't fully capture the essence of the prompt, generate new tags that better fit the user's request. "
                    "Return the result strictly in JSON format with two arrays: 'existed_tags' for matched tags and 'new_tag' for newly generated ones."
                )
            },
            {
                "role": "user",
                "content": f"Analyze this prompt and extract tags: '{prompt}'"
            }
        ],
        "functions": [
            {
                "name": "extract_location_tags",
                "description": (
                    "Extract the most relevant tags based on the user's prompt. "
                    "First, compare the prompt with the existing tags. If any existing tag (or its synonym) matches the prompt, return that tag. "
                    "If no perfect match exists, generate new tags that are unique and non-redundant. "
                    "Do not create synonyms or variations of existing tags when generating new tags."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "existed_tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of tags that match the existing tags"
                        },
                        "new_tag": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of new tags generated from the prompt"
                        }
                    },
                    "required": ["existed_tags", "new_tag"]
                }
            }
        ],
        "function_call": "extract_location_tags",
        "max_tokens": 200,
        "temperature": 0.2,
        "top_p": 0.9,
        "frequency_penalty": 0.8,
        "presence_penalty": 0.3,
        "stream": False
    }

    response = llama.run(api_request_json)
    response_data = response.json()
    content = response_data['choices'][0]['message']['content']

    match = re.search(r'```json\s*(\{.*\})\s*```', content, re.DOTALL)
    if match:
        json_str = match.group(1)
        return json.loads(json_str)
    return None


def compute_bounding_box(lat, lon, radius_m):
    """
    Compute an approximate bounding box around a point (lat, lon) with a given radius (in meters).
    Returns (min_lat, max_lat, min_lon, max_lon).
    """
    R = 6371000  # Earth's radius in meters
    lat_rad = math.radians(lat)
    delta_lat = (radius_m / R) * (180 / math.pi)
    delta_lon = (radius_m / (R * math.cos(lat_rad))) * (180 / math.pi)
    return lat - delta_lat, lat + delta_lat, lon - delta_lon, lon + delta_lon


def filter_by_bounding_box_and_tag(df, user_lat, user_lon, radius_m, search_tag):
    """
    Quickly filter POIs that fall within a bounding box around the user's location
    and contain the specified tag.
    """
    min_lat, max_lat, min_lon, max_lon = compute_bounding_box(
        user_lat, user_lon, radius_m)
    filtered_df = df[
        (df['coordinates.latitude'] >= min_lat) &
        (df['coordinates.latitude'] <= max_lat) &
        (df['coordinates.longitude'] >= min_lon) &
        (df['coordinates.longitude'] <= max_lon)
    ]
    filtered_df = filtered_df[filtered_df['tags'].str.contains(
        search_tag, case=False, na=False)]
    return filtered_df.to_dict(orient='records')


# ---------------------------
# Routing Functions using OSMnx & NetworkX
# ---------------------------
def get_network_graph(user_lat, user_lon, radius_m, travel_mode='drive'):
    """
    Download a street network graph centered on the user's location.
    Supports multiple travel modes like 'drive' and 'walk'.
    """
    graph_dist = radius_m * 2
    try:
        return ox.graph_from_point((user_lat, user_lon), dist=graph_dist, network_type=travel_mode)
    except Exception as e:
        print(f"Error retrieving network graph for {travel_mode}:", e)
        return None


def get_route_distance(graph, user_lat, user_lon, candidate_lat, candidate_lon):
    """
    Compute the route (network) distance between the user's location and the candidate's location.
    Returns distance in meters.
    """
    try:
        user_node = ox.distance.nearest_nodes(graph, user_lon, user_lat)
        candidate_node = ox.distance.nearest_nodes(
            graph, candidate_lon, candidate_lat)
        return nx.shortest_path_length(graph, user_node, candidate_node, weight='length')
    except Exception as e:
        print(
            f"Error computing route for candidate at ({candidate_lat}, {candidate_lon}):", e)
        return float('inf')


def get_top_n_by_route_distance_for_all_modes(candidates, user_lat, user_lon, radius_m, n=5):
    """
    Compute route distances for all candidates using both driving and walking modes.
    """
    modes = ['drive', 'walk']
    all_results = {}
    for mode in modes:
        graph = get_network_graph(
            user_lat, user_lon, radius_m, travel_mode=mode)
        if graph is None:
            print(
                f"Failed to retrieve the network graph for {mode}. Skipping this mode.")
            continue
        for poi in candidates:
            candidate_lat = poi["coordinates.latitude"]
            candidate_lon = poi["coordinates.longitude"]
            poi[f"{mode}_route_distance_m"] = get_route_distance(
                graph, user_lat, user_lon, candidate_lat, candidate_lon)
        candidates_within_radius = [
            poi for poi in candidates if poi[f"{mode}_route_distance_m"] <= radius_m]
        candidates_within_radius.sort(
            key=lambda x: x[f"{mode}_route_distance_m"])
        all_results[mode] = candidates_within_radius[:n]
    return all_results


# ---------------------------
# Data Connection Function
# ---------------------------
def get_poi_data(user_lat, user_lon, radius_m, search_tag):
    """
    Connect to the data source and retrieve POI data.

    Defaults to reading from a CSV file. Can be modified to fetch from a database.
    """
    data_source = os.path.join("datatest", "filtered", "filtered_tags.csv")

    try:
        df = pd.read_csv(data_source)
    except Exception as e:
        print(f"Error reading data from {data_source}: {e}")
        return []

    return filter_by_bounding_box_and_tag(df, user_lat, user_lon, radius_m, search_tag)


# ---------------------------
# Main Query Function
# ---------------------------
def find_top_candidates(user_lat, user_lon, radius_m, search_tag, n=5):
    """
    Find the top candidate POIs given user parameters.

    Parameters:
      user_lat (float): User's latitude.
      user_lon (float): User's longitude.
      radius_m (int): Search radius in meters.
      search_tag (str): Tag to filter POIs.
      n (int): Number of top candidates to return for each travel mode.

    Returns:
      Dictionary with 'drive' and 'walk' keys containing the top candidates with all their info.


    """
    candidates = get_poi_data(user_lat,
                              user_lon, radius_m, search_tag)

    if not candidates:
        print("No candidates found after initial filtering.")
        return {}

    top_candidates = get_top_n_by_route_distance_for_all_modes(
        candidates, user_lat, user_lon, radius_m, n)
    return top_candidates


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

# Initialize the LlamaAPI SDK
llama = LlamaAPI("2048ca26-30cc-4c2e-ad95-fe45e7e1b482")


def get_location_advice(context_text, prompt):
    """
    Sends a request to the Llama API with the provided context information and user prompt.
    The system prompt instructs the AI to base its answer solely on the shared drive and walk mode data,
    and provide advice (e.g. suggesting taxi or walking) without revealing any extra data.
    """
    system_prompt = (
        "You are an AI assistant specialized in providing location suggestions. "
        "Based solely on the following information, analyze the user's request and provide a recommendation. "
        "Do not assume or add any information that is not given. "
        "Here is the available context:\n\n"
        f"{context_text}\n\n"
        "Please advise the user accordingly. For example, if no driving locations are available, suggest using a taxi, car, or walking if possible."
        "Give short answers, without any extra information. always give Name, Cordinate which is latitude and longitude, Distance, Tags"
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

    response = llama.run(api_request_json)
    response_data = response.json()
    # Return the plain text answer provided by the API
    return response_data['choices'][0]['message']['content']


if __name__ == "__main__":
    # Step 1: Define a test prompt for the language model
    test_prompt = "i want to go to somewhere with a great view where i can also drink something"

    # Call llm_api to process the test prompt and display the result
    result = llm_api(test_prompt)
    # print("LLM API Result:")
    # print(json.dumps(result, indent=2))

    # Step 2: Simulated user query parameters (for top candidates search)
    user_lat = 40.985660      # Example: Istanbul city center latitude
    user_lon = 29.027361      # Example: Istanbul city center longitude
    radius_m = 5000           # 5 km search radius
    # only takes the first existed tag, we can change it later to taking a list
    search_tag = result['existed_tags'][0]

    # Step 3: Retrieve top candidates based on the query parameters (both for drive and walk modes)
    top_candidates = find_top_candidates(
        user_lat, user_lon, radius_m, search_tag, n=5)

    # Step 4: Display formatted information for each candidate along with route distances for both modes
    # print("Top Candidates Information:")
    formatted_candidates = format_top_candidates(top_candidates)
    # print(formatted_candidates)

    # Step 5: Use the result from the formatted candidates and test prompt to get location advice
    location_advice = get_location_advice(formatted_candidates, test_prompt)

    # Step 6: Print the location advice result
    print("Location Advice:")
    print(location_advice)
