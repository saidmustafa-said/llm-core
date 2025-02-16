import osmnx as ox
import networkx as nx
import math
import json

# ---------------------------
# Geospatial Utility Functions
# ---------------------------


def compute_bounding_box(lat, lon, radius_m):
    """
    Compute an approximate bounding box around a point (lat, lon) with a given radius (in meters).
    Returns (min_lat, max_lat, min_lon, max_lon).
    """
    R = 6371000  # Earth's radius in meters
    lat_rad = math.radians(lat)

    # Calculate degree offsets
    delta_lat = (radius_m / R) * (180 / math.pi)
    delta_lon = (radius_m / (R * math.cos(lat_rad))) * (180 / math.pi)

    min_lat = lat - delta_lat
    max_lat = lat + delta_lat
    min_lon = lon - delta_lon
    max_lon = lon + delta_lon
    print(lat, lon, radius_m, sep=",")
    print(min_lat, max_lat, min_lon, max_lon, sep=",")
    return min_lat, max_lat, min_lon, max_lon


def filter_by_bounding_box_and_tag(poi_data, user_lat, user_lon, radius_m, search_tag):
    """
    Quickly filter POIs that fall within a bounding box around the user's location
    and contain the specified tag.
    """
    min_lat, max_lat, min_lon, max_lon = compute_bounding_box(
        user_lat, user_lon, radius_m)
    candidates = []

    for poi in poi_data:
        poi_lat = poi["coordinates"]["latitude"]
        poi_lon = poi["coordinates"]["longitude"]
        # Check if within the bounding box
        if min_lat <= poi_lat <= max_lat and min_lon <= poi_lon <= max_lon:
            # Check if the search tag is present (case-insensitive match)
            poi_tags = [tag.lower() for tag in poi.get("tags", [])]
            if search_tag.lower() in poi_tags:
                candidates.append(poi)

    return candidates

# ---------------------------
# Routing Functions using OSMnx & NetworkX (Car Mode)
# ---------------------------


def get_network_graph(user_lat, user_lon, radius_m, travel_mode='drive'):
    """
    Download a street network graph centered on the user's location.
    The search distance is expanded (here, twice the search radius) to ensure coverage.
    For now, we use travel_mode='drive' for car routing.
    """
    graph_dist = radius_m * 2
    try:
        graph = ox.graph_from_point(
            (user_lat, user_lon), dist=graph_dist, network_type=travel_mode)
        return graph
    except Exception as e:
        print("Error retrieving network graph:", e)
        return None


def get_route_distance(graph, user_lat, user_lon, candidate_lat, candidate_lon):
    """
    Compute the route (network) distance between the user's location and the candidate's location.
    Returns distance in meters.
    """
    try:
        # OSMnx expects coordinates in (longitude, latitude) order for nearest_nodes.
        user_node = ox.distance.nearest_nodes(graph, user_lon, user_lat)
        candidate_node = ox.distance.nearest_nodes(
            graph, candidate_lon, candidate_lat)
        # Calculate shortest path length using edge 'length' as weight.
        route_length = nx.shortest_path_length(
            graph, user_node, candidate_node, weight='length')
        return route_length
    except Exception as e:
        print(
            f"Error computing route for candidate at ({candidate_lat}, {candidate_lon}):", e)
        return float('inf')


def get_top_n_by_route_distance(candidates, user_lat, user_lon, radius_m, travel_mode='drive', n=5):
    """
    For each candidate POI, compute the actual route-based distance using the car network.
    Filter candidates to those within the specified route distance and return the top N closest.
    """
    graph = get_network_graph(user_lat, user_lon, radius_m, travel_mode)
    if graph is None:
        print("Failed to retrieve the network graph. Exiting route-based filtering.")
        return []

    # Calculate route distance for each candidate
    for poi in candidates:
        candidate_lat = poi["coordinates"]["latitude"]
        candidate_lon = poi["coordinates"]["longitude"]
        route_distance = get_route_distance(
            graph, user_lat, user_lon, candidate_lat, candidate_lon)
        poi["route_distance_m"] = route_distance

    # Filter to only those POIs that are within the route distance threshold
    candidates_within_radius = [
        poi for poi in candidates if poi["route_distance_m"] <= radius_m]

    # Sort by route distance (shortest first)
    candidates_within_radius.sort(key=lambda x: x["route_distance_m"])

    return candidates_within_radius[:n]


# ---------------------------
# Main Execution: Putting it All Together
# ---------------------------
if __name__ == "__main__":
    # Load the POI data from the JSON file.
    with open('../data/osm_istanbul_relations.json') as f:
        poi_data = json.load(f)

    # Simulated user query parameters:
    user_lat = 40.985660   # Example: Istanbul city center latitude,

    user_lon = 29.027361   # Example: Istanbul city center longitude
    radius_m = 1000        # 5 km search radius for driving
    travel_mode = "drive"  # Car routing mode
    # Example tag to filter for (e.g., museum, attraction, etc.)
    search_tag = "park"

    # --- Step 1: Candidate Filtering by Bounding Box and Tag ---
    candidates = filter_by_bounding_box_and_tag(
        poi_data, user_lat, user_lon, radius_m, search_tag)
    print("Candidates after bounding box and tag filtering:")
    for poi in candidates:
        print(
            f"  {poi['name']} at {poi['coordinates']} with tags: {poi['tags']}")

    # --- Step 2: Geospatial Analysis via Actual Car Routing ---
    top_candidates = get_top_n_by_route_distance(
        candidates, user_lat, user_lon, radius_m, travel_mode, n=5)

    print("\nTop candidates based on car route distances:")
    if top_candidates:
        for poi in top_candidates:
            print(
                f"{poi['name']} - Route Distance: {poi['route_distance_m']:.2f} meters")
    else:
        print("No locations found within the specified route distance.")
