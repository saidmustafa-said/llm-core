from src.logger_setup import get_logger
from src.poi_filter import create_poi_manager
from src.get_top_candidates import create_top_candidates_finder

# Initialize logger context
logger_instance.initialize_logging_context("test_user", 'api_execution')

# Define test parameters
latitude = 41.064108
longitude = 29.031473
search_radius = 2000
search_subcategories = ["restaurant"]

# Create POIManager instance using factory function
poi_manager = create_poi_manager()

# Get POI data
poi_results = poi_manager.get_poi_by_subcategories(
    latitude, longitude, search_radius, search_subcategories)

# Create TopCandidatesFinder instance using factory function
top_candidates_finder = create_top_candidates_finder()

# Run the find_top_candidates function with the obtained POI data
top_candidates = top_candidates_finder.find_top_candidates(
    candidates=poi_results,
    user_lat=latitude,
    user_lon=longitude,
    radius_m=search_radius,
    n=2  # Get the top 5 candidates
)

# Display the top candidates result
print("Top Candidates:", top_candidates)
