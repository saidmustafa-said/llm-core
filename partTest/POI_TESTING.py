
from src.logger_setup import logger_instance
from src.poi_filter import get_poi_data

logger_instance.initialize_logging_context("test_user", 'api_execution')
# Define test parameters
latitude = 41.064108
longitude = 29.031473
search_radius = 2000
search_subcategories = []


# Run the function and print results
poi_results = get_poi_data(
    latitude, longitude, search_radius, search_subcategories)

# Display results
for poi in poi_results:
    print(poi)
