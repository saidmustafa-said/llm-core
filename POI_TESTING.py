import pandas as pd
from unittest.mock import patch, MagicMock
from src.poi_filter import POIManager


def test_poi_manager():
    """Test script for POIManager functionality"""
    print("Starting POIManager test")

    # Define test parameters as variables
    user_lat = 40.9657864
    user_lon = 28.7975449
    radius_m = 1000
    search_subcategories = ['Restaurant', 'Cafe']

    # Create a POIManager instance
    poi_manager = POIManager(dataset="Data/dataset.csv")

    # Test 1: With subcategories - should return FULL ROWS
    print("\nTest 1: Get POI data WITH subcategories (should return full rows)")
    results = poi_manager.get_poi_data(
        user_lat=user_lat,
        user_lon=user_lon,
        radius_m=radius_m,
        search_subcategories=search_subcategories
    )

    print("Returned data:")
    for item in results:
        print("------------------------")
        print(item)
        print("------------------------")

    print("------------------------")
    # Test 2: Without subcategories - should return formatted string
    print("\nTest 2: Get POI data WITHOUT subcategories (should return string)")
    result_string = poi_manager.get_poi_data(
        user_lat=user_lat,
        user_lon=user_lon,
        radius_m=radius_m
    )

    print("Returned string:")
    print(result_string)

    if isinstance(result_string, str) and "amenity:" in result_string:
        print("✓ Correctly returned formatted string")
    else:
        print("✗ Did not get expected string output")


if __name__ == "__main__":
    test_poi_manager()
