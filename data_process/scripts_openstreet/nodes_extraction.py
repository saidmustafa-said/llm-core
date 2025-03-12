import requests
import json

# Overpass API endpoint
url = "https://overpass-api.de/api/interpreter"

# Overpass query for nodes in Istanbul with various tags.
# query = """
# [out:json][timeout:60];
# area["name"="İstanbul"]->.searchArea;
# (
#   // --- Tourism nodes (17) ---
#   node["tourism"="attraction"](area.searchArea);
#   node["tourism"="museum"](area.searchArea);
#   node["tourism"="theme_park"](area.searchArea);
#   node["tourism"="water_park"](area.searchArea);
#   node["tourism"="aquarium"](area.searchArea);
#   node["tourism"="gallery"](area.searchArea);
#   node["tourism"="information"](area.searchArea);
#   node["tourism"="viewpoint"](area.searchArea);
#   node["tourism"="zoo"](area.searchArea);
#   node["tourism"="hotel"](area.searchArea);
#   node["tourism"="guest_house"](area.searchArea);
#   node["tourism"="alpine_hut"](area.searchArea);
#   node["tourism"="artwork"](area.searchArea);
#   node["tourism"="camp_site"](area.searchArea);
#   node["tourism"="picnic_site"](area.searchArea);
#   node["tourism"="hostel"](area.searchArea);
#   node["tourism"="chalet"](area.searchArea);

#   // --- Historic nodes (17) ---
#   node["historic"](area.searchArea);
#   node["historic"="castle"](area.searchArea);
#   node["historic"="monument"](area.searchArea);
#   node["historic"="ruins"](area.searchArea);
#   node["historic"="archaeological_site"](area.searchArea);
#   node["historic"="memorial"](area.searchArea);
#   node["historic"="fort"](area.searchArea);
#   node["historic"="city_gate"](area.searchArea);
#   node["historic"="statue"](area.searchArea);
#   node["historic"="church"](area.searchArea);
#   node["historic"="mosque"](area.searchArea);
#   node["historic"="synagogue"](area.searchArea);
#   node["historic"="temple"](area.searchArea);
#   node["historic"="tower"](area.searchArea);
#   node["historic"="boundary_stone"](area.searchArea);
#   node["historic"="lighthouse"](area.searchArea);
#   node["historic"="battlefield"](area.searchArea);

#   // --- Leisure nodes (12) ---
#   node["leisure"="park"](area.searchArea);
#   node["leisure"="garden"](area.searchArea);
#   node["leisure"="sports_centre"](area.searchArea);
#   node["leisure"="stadium"](area.searchArea);
#   node["leisure"="amusement_park"](area.searchArea);
#   node["leisure"="water_park"](area.searchArea);
#   node["leisure"="swimming_pool"](area.searchArea);
#   node["leisure"="picnic_site"](area.searchArea);
#   node["leisure"="track"](area.searchArea);
#   node["leisure"="fitness_centre"](area.searchArea);
#   node["leisure"="miniature_golf"](area.searchArea);
#   node["leisure"="playground"](area.searchArea);

#   // --- Amenity nodes (39) ---
#   node["amenity"="restaurant"](area.searchArea);
#   node["amenity"="cafe"](area.searchArea);
#   node["amenity"="pub"](area.searchArea);
#   node["amenity"="bar"](area.searchArea);
#   node["amenity"="fast_food"](area.searchArea);
#   node["amenity"="ice_cream"](area.searchArea);
#   node["amenity"="bank"](area.searchArea);
#   node["amenity"="pharmacy"](area.searchArea);
#   node["amenity"="post_office"](area.searchArea);
#   node["amenity"="toilets"](area.searchArea);
#   node["amenity"="hospital"](area.searchArea);
#   node["amenity"="clinic"](area.searchArea);
#   node["amenity"="theatre"](area.searchArea);
#   node["amenity"="cinema"](area.searchArea);
#   node["amenity"="library"](area.searchArea);
#   node["amenity"="parking"](area.searchArea);
#   node["amenity"="fuel"](area.searchArea);
#   node["amenity"="barber"](area.searchArea);
#   node["amenity"="hairdresser"](area.searchArea);
#   node["amenity"="dentist"](area.searchArea);
#   node["amenity"="doctor"](area.searchArea);
#   node["amenity"="embassy"](area.searchArea);
#   node["amenity"="police"](area.searchArea);
#   node["amenity"="fire_station"](area.searchArea);
#   node["amenity"="post_box"](area.searchArea);
#   node["amenity"="bench"](area.searchArea);
#   node["amenity"="drinking_water"](area.searchArea);
#   node["amenity"="recycling"](area.searchArea);
#   node["amenity"="vending_machine"](area.searchArea);
#   node["amenity"="townhall"](area.searchArea);
#   node["amenity"="fountain"](area.searchArea);
#   node["amenity"="marketplace"](area.searchArea);
#   node["amenity"="shelter"](area.searchArea);
#   node["amenity"="bus_station"](area.searchArea);
#   node["amenity"="taxi"](area.searchArea);
#   node["amenity"="bicycle_parking"](area.searchArea);
#   node["amenity"="charging_station"](area.searchArea);
#   node["amenity"="waste_basket"](area.searchArea);
#   node["amenity"="atm"](area.searchArea);

#   // --- Shop nodes (11) ---
#   node["shop"="souvenir"](area.searchArea);
#   node["shop"="gift"](area.searchArea);
#   node["shop"="clothes"](area.searchArea);
#   node["shop"="bakery"](area.searchArea);
#   node["shop"="convenience"](area.searchArea);
#   node["shop"="supermarket"](area.searchArea);
#   node["shop"="jewelry"](area.searchArea);
#   node["shop"="antiques"](area.searchArea);
#   node["shop"="confectionery"](area.searchArea);
#   node["shop"="butcher"](area.searchArea);
#   node["shop"="organic"](area.searchArea);

#   // --- Additional nodes (4) ---
#   node["leisure"="sauna"](area.searchArea);
#   node["amenity"="bbq"](area.searchArea);
#   node["man_made"="bridge"](area.searchArea);
#   node["historic"="stele"](area.searchArea);
# );
# out body;
# """


query = """
[out:json][timeout:60];
area["name"="İstanbul"]->.searchArea;
(
  node["leisure"="sauna"](area.searchArea);
  node["amenity"="bbq"](area.searchArea);
  node["man_made"="bridge"](area.searchArea);
  node["historic"="stele"](area.searchArea);
);
out body;
"""

print("📡 Sending node query to Overpass API...")
response = requests.get(url, params={"data": query})

if response.status_code == 200:
    data = response.json()
    places = []
    
    # Process each node element
    for element in data.get("elements", []):
        if "lat" in element and "lon" in element:
            lat = element["lat"]
            lon = element["lon"]
        else:
            continue
        
        tags = element.get("tags", {})
        name = tags.get("name", "Unknown Place")
        description = tags.get("description", "No description available")
        location = tags.get("addr:city", "Türkiye/İstanbul")
        
        # Optionally extract a list of key tags for further classification
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
    
    # Save the processed nodes data to a JSON file
    with open("../../new_data/nodes/others.json", "w", encoding="utf-8") as f:
        json.dump(places, f, ensure_ascii=False, indent=4)
    
    print("✅ Node data extracted and saved to 'osm_istanbul_nodes.json'.")
else:
    print("❌ API request failed with status code:", response.status_code)
