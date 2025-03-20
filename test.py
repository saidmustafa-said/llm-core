from src.llamarequest import llm_api
from src.poi_filter import get_poi_data
from src.get_top_candidates import find_top_candidates
from src.get_location_advice import get_location_advice


# Define input variables for easier testing
user_prompt = "i want to go to somewhere with a great view where i can drink some tea and have some good food"
latitude = 41.064108
longitude = 29.031473
search_radius = 2000
num_candidates = 2

# Step 1: Extract tags from prompt
result = llm_api(user_prompt)
search_category = result['subcategories']['findings']
search_tag = result['tags']['existed']


# print()
# print()
# print()
# print("Extracted Tags:", result)
# print()
# print()
# print()

# Step 2: Fetch candidate POIs
candidates = get_poi_data(latitude, longitude, search_radius, search_category)
top_candidates = find_top_candidates(
    candidates, latitude, longitude, search_radius, num_candidates)

print()
print()
print()
print("Top Candidates:", top_candidates)
print()
print()
print()


# Step 3: Get location advice
location_advice = get_location_advice(top_candidates, user_prompt)

print()
print()
print()
print("Location Advice:", location_advice)
print()
print()
print()

