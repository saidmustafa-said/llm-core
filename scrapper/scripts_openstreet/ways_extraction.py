import requests
import json

# Overpass API endpoint
url = "https://overpass-api.de/api/interpreter"

# Overpass query for ways in Istanbul.
# Using 'out center' ensures that a center coordinate is returned for each way.
query = """
[out:json][timeout:120];
area["name"="İstanbul"]->.searchArea;
(
  way["historic"="wayside_cross"](area.searchArea);
  way["historic"="battlefield"](area.searchArea);
  way["tourism"="festival"](area.searchArea);
  way["amenity"="fire_station"](area.searchArea);
  way["amenity"="police"](area.searchArea);
  way["leisure"="golf_course"](area.searchArea);
  way["leisure"="nature_reserve"](area.searchArea);
  way["leisure"="arboretum"](area.searchArea);
  way["amenity"="toilets"](area.searchArea);
  way["amenity"="water_point"](area.searchArea);
  way["shop"="bakery"](area.searchArea);
  way["shop"="butcher"](area.searchArea);
  way["shop"="cheese"](area.searchArea);
  way["shop"="wine"](area.searchArea);
  way["shop"="deli"](area.searchArea);
);
out center;
"""

# query = """
# [out:json][timeout:120];
# area["name"="İstanbul"]->.searchArea;
# (
#   /* Tourism-related features */
#   way["tourism"="attraction"](area.searchArea);
#   way["tourism"="museum"](area.searchArea);
#   way["tourism"="theme_park"](area.searchArea);
#   way["tourism"="water_park"](area.searchArea);
#   way["tourism"="artwork"](area.searchArea);
#   way["tourism"="viewpoint"](area.searchArea);
#   way["tourism"="zoo"](area.searchArea);
#   way["tourism"="guest_house"](area.searchArea);
#   way["tourism"="alpine_hut"](area.searchArea);
#   way["tourism"="information"](area.searchArea);

#   /* Historic features */
#   way["historic"="monument"](area.searchArea);
#   way["historic"="castle"](area.searchArea);
#   way["historic"="archaeological_site"](area.searchArea);
#   way["historic"="ruins"](area.searchArea);
#   way["historic"="memorial"](area.searchArea);
#   way["historic"="fort"](area.searchArea);
#   way["historic"="manor"](area.searchArea);
#   way["historic"="city_wall"](area.searchArea);
#   way["historic"="tower"](area.searchArea);
#   way["historic"="industrial"](area.searchArea);

#   /* Leisure features */
#   way["leisure"="park"](area.searchArea);
#   way["leisure"="garden"](area.searchArea);
#   way["leisure"="picnic_site"](area.searchArea);
#   way["leisure"="stadium"](area.searchArea);
#   way["leisure"="sports_centre"](area.searchArea);
#   way["leisure"="swimming_pool"](area.searchArea);
#   way["leisure"="track"](area.searchArea);
#   way["leisure"="playground"](area.searchArea);
#   way["leisure"="water_park"](area.searchArea);
#   way["leisure"="marina"](area.searchArea);

#   /* Amenity features */
#   way["amenity"="cafe"](area.searchArea);
#   way["amenity"="restaurant"](area.searchArea);
#   way["amenity"="fast_food"](area.searchArea);
#   way["amenity"="bar"](area.searchArea);
#   way["amenity"="pub"](area.searchArea);
#   way["amenity"="bakery"](area.searchArea);
#   way["amenity"="ice_cream"](area.searchArea);
#   way["amenity"="bank"](area.searchArea);
#   way["amenity"="theatre"](area.searchArea);
#   way["amenity"="cinema"](area.searchArea);

#   /* Shop features */
#   way["shop"="souvenir"](area.searchArea);
#   way["shop"="gift"](area.searchArea);
#   way["shop"="craft"](area.searchArea);

#   /* Natural features */
#   way["natural"="peak"](area.searchArea);
#   way["natural"="waterfall"](area.searchArea);
#   way["natural"="wood"](area.searchArea);
#   way["natural"="tree"](area.searchArea);
#   way["natural"="scrub"](area.searchArea);

#   /* Man-made features */
#   way["man_made"="tower"](area.searchArea);
#   way["man_made"="bridge"](area.searchArea);
#   way["man_made"="lighthouse"](area.searchArea);
#   way["man_made"="obelisk"](area.searchArea);
#   way["man_made"="pyramid"](area.searchArea);
#   way["man_made"="silo"](area.searchArea);
#   way["man_made"="water_tower"](area.searchArea);
#   way["man_made"="mast"](area.searchArea);

#   /* Additional tourism & mixed tags */
#   way["tourism"="camp_site"](area.searchArea);
#   way["tourism"="picnic_site"](area.searchArea);
#   way["amenity"="fountain"](area.searchArea);
#   way["amenity"="shelter"](area.searchArea);
#   way["leisure"="fitness_station"](area.searchArea);
#   way["leisure"="bandstand"](area.searchArea);
#   way["leisure"="miniature_golf"](area.searchArea);
#   way["leisure"="dog_park"](area.searchArea);
#   way["amenity"="marketplace"](area.searchArea);
#   way["amenity"="library"](area.searchArea);
#   way["amenity"="pharmacy"](area.searchArea);
#   way["amenity"="townhall"](area.searchArea);
#   way["amenity"="post_office"](area.searchArea);

#   /* More historic features */
#   way["historic"="church"](area.searchArea);
#   way["historic"="mosque"](area.searchArea);
#   way["historic"="synagogue"](area.searchArea);
#   way["historic"="shrine"](area.searchArea);

#   /* Extra leisure & amenity entries */
#   way["leisure"="ice_rink"](area.searchArea);
#   way["amenity"="parking"](area.searchArea);
#   way["amenity"="clinic"](area.searchArea);
#   way["leisure"="bowling_alley"](area.searchArea);
#   way["amenity"="casino"](area.searchArea);
#   way["amenity"="nightclub"](area.searchArea);
#   way["amenity"="community_centre"](area.searchArea);
#   way["amenity"="college"](area.searchArea);
#   way["amenity"="university"](area.searchArea);
#   way["amenity"="kindergarten"](area.searchArea);
#   way["amenity"="school"](area.searchArea);
#   way["amenity"="drinking_water"](area.searchArea);

#   /* Further historic tags */
#   way["historic"="wayside_cross"](area.searchArea);
#   way["historic"="battlefield"](area.searchArea);

#   /* One more tourism feature */
#   way["tourism"="festival"](area.searchArea);

#   /* Additional infrastructure and leisure/shop extras */
#   way["amenity"="fire_station"](area.searchArea);
#   way["amenity"="police"](area.searchArea);
#   way["leisure"="golf_course"](area.searchArea);
#   way["leisure"="nature_reserve"](area.searchArea);
#   way["leisure"="arboretum"](area.searchArea);
#   way["amenity"="toilets"](area.searchArea);
#   way["amenity"="water_point"](area.searchArea);
#   way["shop"="bakery"](area.searchArea);
#   way["shop"="butcher"](area.searchArea);
#   way["shop"="cheese"](area.searchArea);
#   way["shop"="wine"](area.searchArea);
#   way["shop"="deli"](area.searchArea);
# );
# out center;
# """

print("📡 Sending ways query to Overpass API...")
response = requests.get(url, params={"data": query})

if response.status_code == 200:
    data = response.json()
    places = []
    
    # Process each way element (using its center for coordinates)
    for element in data.get("elements", []):
        if "center" in element:
            lat = element["center"]["lat"]
            lon = element["center"]["lon"]
        else:
            continue
        
        tags = element.get("tags", {})
        name = tags.get("name", "Unknown Place")
        description = tags.get("description", "No description available")
        location = tags.get("addr:city", "Türkiye/İstanbul")
        
        tag_keys = ["tourism", "historic", "leisure", "amenity"]
        tags_list = [tags.get(key) for key in tag_keys if key in tags]
        
        place = {
            "name": name,
            "description": description,
            "location": location,
            "coordinates": {"latitude": lat, "longitude": lon},
            "tags": tags_list
            # "multimedia": {"images": [], "videos": []},
            # "accessibility": {"parking": False, "wheelchair_accessible": False},
            # "reviews": {"rating": 0, "sentiment": []},
            # "best_time_to_visit": {"season": "", "time_of_day": ""}
        }
        places.append(place)
    
    # Save the processed ways data to a JSON file
    with open("../../new_data/ways/others.json", "w", encoding="utf-8") as f:
        json.dump(places, f, ensure_ascii=False, indent=4)
    
    print("✅ Way data extracted and saved to 'ways'.")
else:
    print("❌ API request failed with status code:", response.status_code)

