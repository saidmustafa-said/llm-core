from utils import timing_decorator
import os
import pandas as pd
import math

@timing_decorator
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


@timing_decorator
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


@timing_decorator
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
