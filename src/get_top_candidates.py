from src.utils import timing_decorator
from osmnx import graph_from_point, distance
import networkx as nx
from functools import lru_cache

cached_graph = {}


@lru_cache(maxsize=128)
def get_node_for_coords(graph, lat, lon):
    return distance.nearest_nodes(graph, lon, lat)

@timing_decorator
def get_route_distance(graph, user_lat, user_lon, candidate_lat, candidate_lon):
    """
    Compute the route (network) distance between the user's location and the candidate's location.
    Returns distance in meters.
    """
    try:
        # Önbelleğe alınmış node hesaplamalarını kullan
        user_node = get_node_for_coords(graph, user_lat, user_lon)
        candidate_node = get_node_for_coords(
            graph, candidate_lat, candidate_lon)

        # Kısa yolu hesapla
        return nx.shortest_path_length(graph, user_node, candidate_node, weight='length')

    except Exception as e:
        print(
            f"Error computing route for candidate at ({candidate_lat}, {candidate_lon}):", e)
        return float('inf')


@timing_decorator
def get_network_graph(user_lat, user_lon, radius_m, travel_mode='drive'):
    graph_key = (user_lat, user_lon, radius_m, travel_mode)

    # Önbellekte varsa, döndür
    if graph_key in cached_graph:
        print("Returning cached graph")
        return cached_graph[graph_key]

    # Önbellekte yoksa, veriyi al
    try:
        graph_dist = radius_m * 2
        graph = graph_from_point(
            (user_lat, user_lon), dist=graph_dist, network_type=travel_mode)
        cached_graph[graph_key] = graph  # Önbelleğe kaydet
        return graph
    except Exception as e:
        print(f"Error retrieving network graph for {travel_mode}:", e)
        return None





@timing_decorator
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


@timing_decorator
def find_top_candidates(candidates, user_lat, user_lon, radius_m, search_tag, n=5):
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

    if not candidates:
        print("No candidates found after initial filtering.")
        return {}

    top_candidates = get_top_n_by_route_distance_for_all_modes(
        candidates, user_lat, user_lon, radius_m, n)
    return top_candidates
