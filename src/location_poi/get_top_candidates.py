from src.utils.utils import timing_decorator
from osmnx import graph_from_point, distance
import networkx as nx
from functools import lru_cache
from collections import OrderedDict
import concurrent.futures
from src.core.data_types import POIData, TopCandidates
from typing import List, Dict
from src.location_poi.interfaces.top_candidates import ITopCandidatesFinder
import numpy as np

# Limited-size cache for graphs
MAX_CACHE_SIZE = 50
cached_graph = OrderedDict()

# Enhanced cache for node coordinates


def validate_poi_data(poi: Dict) -> POIData:
    required_keys = {'latitude', 'longitude', 'subcategory'}
    if not required_keys.issubset(poi.keys()):
        missing = required_keys - poi.keys()
        raise ValueError(f"Invalid POI data, missing keys: {missing}")
    return POIData(poi)


def validate_top_candidates(candidates: Dict) -> TopCandidates:
    valid_modes = {'drive', 'walk'}
    return TopCandidates({
        mode: [validate_poi_data(poi) for poi in candidates.get(mode, [])]
        for mode in valid_modes
    })


@lru_cache(maxsize=256)
def get_node_for_coords(graph, lat, lon):
    """Finds the nearest node in the graph for given coordinates."""
    return distance.nearest_nodes(graph, lon, lat)


def get_route_distance(graph, user_lat, user_lon, candidate_lat, candidate_lon):
    """Computes the network distance between user and candidate."""
    try:
        user_node = get_node_for_coords(graph, user_lat, user_lon)
        candidate_node = get_node_for_coords(
            graph, candidate_lat, candidate_lon)

        # Check if nodes exist and are connected before running expensive algorithms
        if user_node not in graph or candidate_node not in graph:
            return float('inf')

        # Quick check if user and candidate are the same node
        if user_node == candidate_node:
            return 0.0

        # Use A* algorithm which is typically faster than Dijkstra for point-to-point
        try:
            path_length = nx.astar_path_length(
                graph, user_node, candidate_node, weight='length')
            return path_length
        except nx.NetworkXNoPath:
            return float('inf')

    except Exception as e:
        print(
            f"Error computing route for ({candidate_lat}, {candidate_lon}):", e)
        return float('inf')


def cache_graph(graph_key, graph):
    """Manages graph cache with a limited size."""
    if len(cached_graph) >= MAX_CACHE_SIZE:
        cached_graph.popitem(last=False)  # Remove oldest entry
    cached_graph[graph_key] = graph


@timing_decorator
def get_network_graph(user_lat, user_lon, radius_m, travel_mode):
    """Retrieves or builds a network graph for the given location and mode."""
    graph_key = (user_lat, user_lon, radius_m, travel_mode)

    if graph_key in cached_graph:
        print("Returning cached graph")
        return cached_graph[graph_key]

    try:
        # Use smaller graph radius for walking mode
        if travel_mode == 'walk':
            # Walking usually needs smaller area
            graph_dist = min(radius_m * 1.5, 2000)
        else:
            # Limit maximum size for driving
            graph_dist = min(radius_m * 2, 5000)

        # Use lower simplify setting for walking and higher for driving
        simplify = travel_mode != 'walk'

        graph = graph_from_point(
            (user_lat, user_lon),
            dist=graph_dist,
            network_type=travel_mode,
            simplify=simplify
        )

        # Extract the largest connected component
        if nx.is_directed(graph):
            largest_component = max(
                nx.strongly_connected_components(graph), key=len)
        else:
            largest_component = max(nx.connected_components(
                graph.to_undirected()), key=len)

        graph = graph.subgraph(largest_component).copy()

        cache_graph(graph_key, graph)
        return graph

    except Exception as e:
        print(f"Error retrieving network graph for {travel_mode}:", e)
        return None


def process_candidate(args):
    """Process a single candidate - used for parallel processing."""
    graph, user_lat, user_lon, poi, travel_mode, radius_m = args
    try:
        candidate_lat = poi["latitude"]
        candidate_lon = poi["longitude"]

        route_distance = get_route_distance(
            graph, user_lat, user_lon, candidate_lat, candidate_lon)

        if route_distance == float('inf') or route_distance > radius_m:
            return None

        poi_copy = poi.copy()
        poi_copy[f"{travel_mode}_route_distance_m"] = route_distance

        if poi_copy:
            return validate_poi_data(poi_copy)
        return None
    except KeyError as e:
        print(f"KeyError: Missing column {e} in candidate POI data.")
        return None


def get_top_n_by_route_distance_for_all_modes(candidates, user_lat, user_lon, radius_m, n=5):
    """Computes route distances for all candidates for both driving and walking modes."""
    modes = ['drive', 'walk']
    all_results = {}

    for mode in modes:
        graph = get_network_graph(
            user_lat, user_lon, radius_m, travel_mode=mode)
        if graph is None:
            print(
                f"Failed to retrieve the network graph for {mode}. Skipping.")
            continue

        # Prepare arguments for parallel processing
        args_list = [(graph, user_lat, user_lon, poi, mode, radius_m)
                     for poi in candidates]

        # Use ThreadPoolExecutor for parallelization
        valid_candidates = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(32, len(candidates))) as executor:
            for result in executor.map(process_candidate, args_list):
                if result is not None:
                    valid_candidates.append(result)

        # Sort and select the top N candidates
        valid_candidates.sort(key=lambda x: x[f"{mode}_route_distance_m"])
        all_results[mode] = valid_candidates[:n]

    return all_results


@timing_decorator
def find_top_candidates(candidates: List[POIData], user_lat: float, user_lon: float,
                        radius_m: int, n: int) -> TopCandidates:
    """Finds the top candidate POIs based on route distance.

    Returns:
        Dict containing:
        - drive: List[POIData] - Top candidates for driving mode
        - walk: List[POIData] - Top candidates for walking mode
        Each POIData contains:
        - name: Optional[str] - Name of the POI
        - latitude: float - Latitude coordinate
        - longitude: float - Longitude coordinate
        - subcategory: str - Category of the POI
        - address: Optional[str] - Address of the POI
        - score: Optional[float] - Relevance score
        - drive_route_distance_m: Optional[float] - Driving distance in meters
        - walk_route_distance_m: Optional[float] - Walking distance in meters
    """
    if not candidates:
        print("No candidates found.")
        return {}

    # If there are too many candidates, pre-filter using Euclidean distance
    if len(candidates) > 50:
        prefiltered_candidates = prefilter_candidates_by_distance(
            candidates, user_lat, user_lon, radius_m * 1.5)
        return get_top_n_by_route_distance_for_all_modes(
            prefiltered_candidates, user_lat, user_lon, radius_m, n)

    all_results = get_top_n_by_route_distance_for_all_modes(
        candidates, user_lat, user_lon, radius_m, n)
    return validate_top_candidates(all_results)


def prefilter_candidates_by_distance(candidates, user_lat, user_lon, max_distance_m):
    """Pre-filter candidates using Euclidean distance to reduce computation."""
    from math import radians, sin, cos, sqrt, atan2

    # Define the Haversine formula for distance calculation
    def haversine_distance(lat1, lon1, lat2, lon2):
        R = 6371000  # Earth radius in meters

        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c

    # Calculate distances and filter
    filtered_candidates = []
    for poi in candidates:
        try:
            distance = haversine_distance(
                user_lat, user_lon, poi["latitude"], poi["longitude"])
            if distance <= max_distance_m:
                filtered_candidates.append(poi)
        except KeyError:
            continue

    print(
        f"Pre-filtered from {len(candidates)} to {len(filtered_candidates)} candidates")
    return filtered_candidates


class TopCandidatesFinder:
    def __init__(self):
        pass

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the Haversine distance between two points in meters.
        """
        R = 6371000  # Earth's radius in meters
        phi1 = np.radians(lat1)
        phi2 = np.radians(lat2)
        delta_phi = np.radians(lat2 - lat1)
        delta_lambda = np.radians(lon2 - lon1)

        a = np.sin(delta_phi/2)**2 + np.cos(phi1) * \
            np.cos(phi2) * np.sin(delta_lambda/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        return R * c

    @timing_decorator
    def find_top_candidates(self, candidates: List[POIData], user_lat: float, user_lon: float,
                            radius_m: int, n: int = 4) -> TopCandidates:
        """
        Find the top n candidates from a list of POIs based on various criteria.

        Args:
            candidates: List of POI data to filter
            user_lat: User's latitude
            user_lon: User's longitude
            radius_m: Search radius in meters
            n: Number of top candidates to return (default: 4)

        Returns:
            TopCandidates object containing lists of POIs for different modes
        """
        if not candidates:
            return TopCandidates(drive=[], walk=[])

        # Calculate distances for all candidates
        for candidate in candidates:
            distance = self.calculate_distance(
                user_lat, user_lon, candidate['latitude'], candidate['longitude'])
            candidate['distance_m'] = distance

        # Sort candidates by distance
        sorted_candidates = sorted(candidates, key=lambda x: x['distance_m'])

        # Take top n candidates
        top_candidates = sorted_candidates[:n]

        # Create TopCandidates object
        return TopCandidates(
            drive=top_candidates,
            walk=top_candidates
        )


def create_top_candidates_finder() -> ITopCandidatesFinder:
    """
    Factory function to create a TopCandidatesFinder instance.

    Returns:
        An instance of TopCandidatesFinder implementing the ITopCandidatesFinder interface.
    """
    return TopCandidatesFinder()
