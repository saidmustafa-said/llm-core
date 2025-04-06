from src.utils import timing_decorator
import pandas as pd
import math
import re
from config import DATASET
from src.data_types import POIData
from typing import List, Dict, Optional


class POIManager:
    def __init__(self, dataset: str = DATASET):
        self.dataset = dataset
        self.df = None

    def load_data(self):
        """Loads the dataset if it has not already been loaded."""
        if self.df is None:
            try:
                self.df = pd.read_csv(self.dataset)
                print("Columns in dataset:", self.df.columns)
            except Exception as e:
                print(f"Error reading data from {self.dataset}: {e}")
                self.df = pd.DataFrame()

    @staticmethod
    def compute_bounding_box(lat: float, lon: float, radius_m: int):
        """
        Compute a bounding box (min/max latitude and longitude)
        given a central point and radius in meters.
        """
        R = 6371000  # Earth's radius in meters
        lat_rad = math.radians(lat)
        delta_lat = (radius_m / R) * (180 / math.pi)
        delta_lon = (radius_m / (R * math.cos(lat_rad))) * (180 / math.pi)
        return lat - delta_lat, lat + delta_lat, lon - delta_lon, lon + delta_lon

    @staticmethod
    def validate_poi_data(poi: Dict) -> POIData:
        """
        Validates that the given dictionary has the required keys and
        converts it into a POIData instance.
        """
        required_keys = {'latitude', 'longitude', 'subcategory'}
        if not required_keys.issubset(poi.keys()):
            missing = required_keys - poi.keys()
            raise ValueError(f"Invalid POI data, missing keys: {missing}")
        return POIData(poi)

    def filter_by_bounding_box_and_subcategory(self, user_lat: float, user_lon: float,
                                               radius_m: int, search_subcategories: List[str]) -> List[POIData]:
        """
        Filters locations by geographic bounding box and a list of subcategories.
        """
        min_lat, max_lat, min_lon, max_lon = self.compute_bounding_box(
            user_lat, user_lon, radius_m)

        # Ensure required columns exist
        required_columns = {'latitude', 'longitude', 'subcategory'}
        missing_columns = required_columns - set(self.df.columns)
        if missing_columns:
            print(
                f"Error: Missing required columns in dataset: {missing_columns}")
            print("Available columns:", self.df.columns)
            return []

        # Filter by geographic bounding box
        filtered_df = self.df[
            (self.df['latitude'] >= min_lat) & (self.df['latitude'] <= max_lat) &
            (self.df['longitude'] >= min_lon) & (
                self.df['longitude'] <= max_lon)
        ]

        # Filter by multiple subcategories
        if search_subcategories:
            pattern = "|".join(map(re.escape, search_subcategories))
            filtered_df = filtered_df[filtered_df['subcategory'].str.contains(
                pattern, case=False, na=False)]

        # Validate and wrap each POI into a POIData instance
        return [self.validate_poi_data(poi) for poi in filtered_df.to_dict(orient='records')]

    @timing_decorator
    def get_poi_data(self, user_lat: float, user_lon: float, radius_m: int,
                     search_subcategories: Optional[List[str]] = None):
        """
        Retrieves Points of Interest (POI) data filtered by location.

        - If `search_subcategories` is provided, it returns filtered POI objects.
        - If `search_subcategories` is omitted, it returns a formatted string that maps each category to its
        unique subcategories, where all values are strings.
        """
        self.load_data()

        # When specific subcategories are provided, filter and return POI objects.
        if search_subcategories:
            print("Categories to search for:", search_subcategories)
            return self.filter_by_bounding_box_and_subcategory(user_lat, user_lon, radius_m, search_subcategories)
        else:
            # Ensure the dataset has the required columns for mapping.
            required_columns = {'latitude',
                                'longitude', 'subcategory', 'category'}
            missing_columns = required_columns - set(self.df.columns)
            if missing_columns:
                print(
                    f"Error: Missing required columns in dataset: {missing_columns}")
                print("Available columns:", self.df.columns)
                return ""

            min_lat, max_lat, min_lon, max_lon = self.compute_bounding_box(
                user_lat, user_lon, radius_m)
            filtered_df = self.df[
                (self.df['latitude'] >= min_lat) & (self.df['latitude'] <= max_lat) &
                (self.df['longitude'] >= min_lon) & (
                    self.df['longitude'] <= max_lon)
            ]

            # Build a dictionary where each key is a category and the value is a set of subcategories
            category_to_subcategories = {}
            for _, row in filtered_df.iterrows():
                category = str(row['category']).strip()
                subcategory = str(row['subcategory']).strip()
                if not category or not subcategory:
                    continue
                if category not in category_to_subcategories:
                    category_to_subcategories[category] = set()
                category_to_subcategories[category].add(subcategory)

            # Build the final multi-line string
            result_lines = []
            for category, subcategories in category_to_subcategories.items():
                # Sort the subcategories alphabetically for consistency
                subcategories_list = ", ".join(sorted(subcategories))
                result_lines.append(f"{category}: {subcategories_list}")

            final_result = "\n".join(result_lines)
            return final_result
