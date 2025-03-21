from src.utils import timing_decorator
import pandas as pd
import math
from config import DATASET
import re
from src.data_types import POIData
from typing import List
from src.utils import validate_poi_data
from src.data_types import POIData
from typing import Dict

def validate_poi_data(poi: Dict) -> POIData:
    required_keys = {'latitude', 'longitude', 'subcategory'}
    if not required_keys.issubset(poi.keys()):
        missing = required_keys - poi.keys()
        raise ValueError(f"Invalid POI data, missing keys: {missing}")
    return POIData(poi)

@timing_decorator
def compute_bounding_box(lat, lon, radius_m):
    """
    Compute a bounding box (min/max latitude and longitude) given a central point and radius in meters.
    """
    R = 6371000  # Earth's radius in meters
    lat_rad = math.radians(lat)
    delta_lat = (radius_m / R) * (180 / math.pi)
    delta_lon = (radius_m / (R * math.cos(lat_rad))) * (180 / math.pi)
    return lat - delta_lat, lat + delta_lat, lon - delta_lon, lon + delta_lon


@timing_decorator
def filter_by_bounding_box_and_subcategory(df, user_lat, user_lon, radius_m, search_subcategories) -> List[POIData]:
    """
    Filters locations by geographic bounding box and a list of subcategories.
    """
    min_lat, max_lat, min_lon, max_lon = compute_bounding_box(
        user_lat, user_lon, radius_m)

    # Ensure required columns exist
    required_columns = {'latitude', 'longitude', 'subcategory'}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        print(f"Error: Missing required columns in dataset: {missing_columns}")
        print("Available columns:", df.columns)
        return []

    # Filter by geographic bounding box
    filtered_df = df[
        (df['latitude'] >= min_lat) & (df['latitude'] <= max_lat) &
        (df['longitude'] >= min_lon) & (df['longitude'] <= max_lon)
    ]

    # Filter by multiple subcategories
    if search_subcategories:
        # Escape to avoid regex errors
        pattern = "|".join(map(re.escape, search_subcategories))
        filtered_df = filtered_df[filtered_df['subcategory'].str.contains(
            pattern, case=False, na=False)]

    return [validate_poi_data(poi) for poi in filtered_df.to_dict(orient='records')]


@timing_decorator
def get_poi_data(user_lat: float, user_lon: float,
                 radius_m: int, search_subcategories: List[str]) -> List[POIData]:
    """
    Retrieves Points of Interest (POI) data filtered by location and multiple subcategories.
    """
    try:
        print("Categories to search for:", search_subcategories)
        df = pd.read_csv(DATASET)
        print("Columns in dataset:", df.columns)

        return filter_by_bounding_box_and_subcategory(df, user_lat, user_lon, radius_m, search_subcategories)

    except Exception as e:
        print(f"Error reading data from {DATASET}: {e}")
        return []
