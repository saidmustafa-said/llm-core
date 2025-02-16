from flask import Flask, render_template, request, jsonify
import json
import osmnx as ox
import networkx as nx
import math

app = Flask(__name__)

# ---------------------------
# Geospatial Utility Functions
# ---------------------------


def compute_bounding_box(lat, lon, radius_m):
    R = 6371000
    lat_rad = math.radians(lat)
    delta_lat = (radius_m / R) * (180 / math.pi)
    delta_lon = (radius_m / (R * math.cos(lat_rad))) * (180 / math.pi)
    return lat - delta_lat, lat + delta_lat, lon - delta_lon, lon + delta_lon


def filter_by_bounding_box_and_tag(poi_data, user_lat, user_lon, radius_m, search_tag):
    min_lat, max_lat, min_lon, max_lon = compute_bounding_box(
        user_lat, user_lon, radius_m)
    candidates = []
    for poi in poi_data:
        poi_lat = poi["coordinates"]["latitude"]
        poi_lon = poi["coordinates"]["longitude"]
        if min_lat <= poi_lat <= max_lat and min_lon <= poi_lon <= max_lon:
            poi_tags = [tag.lower() for tag in poi.get("tags", [])]
            if search_tag.lower() in poi_tags:
                candidates.append(poi)
    return candidates


def get_network_graph(user_lat, user_lon, radius_m, travel_mode='drive'):
    graph_dist = radius_m * 2
    try:
        return ox.graph_from_point((user_lat, user_lon), dist=graph_dist, network_type=travel_mode)
    except Exception as e:
        print("Error:", e)
        return None


def get_route_distance(graph, user_lat, user_lon, candidate_lat, candidate_lon):
    try:
        user_node = ox.distance.nearest_nodes(graph, user_lon, user_lat)
        candidate_node = ox.distance.nearest_nodes(
            graph, candidate_lon, candidate_lat)
        return nx.shortest_path_length(graph, user_node, candidate_node, weight='length')
    except:
        return float('inf')


def get_top_n_by_route_distance(candidates, user_lat, user_lon, radius_m, travel_mode='drive', n=5):
    graph = get_network_graph(user_lat, user_lon, radius_m, travel_mode)
    if not graph:
        return []

    for poi in candidates:
        poi["route_distance_m"] = get_route_distance(graph, user_lat, user_lon,
                                                     poi["coordinates"]["latitude"],
                                                     poi["coordinates"]["longitude"])

    return sorted([p for p in candidates if p["route_distance_m"] <= radius_m], key=lambda x: x["route_distance_m"])[:n]

# ---------------------------
# Flask Routes
# ---------------------------


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    data = request.json
    user_lat = float(data["latitude"])
    user_lon = float(data["longitude"])
    radius_m = int(data["radius"])
    search_tag = data["tag"]

    with open('data/osm_istanbul_relations.json') as f:
        poi_data = json.load(f)

    candidates = filter_by_bounding_box_and_tag(
        poi_data, user_lat, user_lon, radius_m, search_tag)
    results = get_top_n_by_route_distance(
        candidates, user_lat, user_lon, radius_m)

    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True)
