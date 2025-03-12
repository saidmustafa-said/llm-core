import requests
import json

# Overpass API endpoint
url = "https://overpass-api.de/api/interpreter"

# [out:json][timeout:120];
# area["name"="İstanbul"]->.searchArea;
# (
#   // --- Tourism-related features ---
#   relation["tourism"="attraction"](area.searchArea);
#   relation["tourism"="museum"](area.searchArea);
#   relation["tourism"="gallery"](area.searchArea);
#   relation["tourism"="zoo"](area.searchArea);
#   relation["tourism"="information"](area.searchArea);
#   relation["tourism"="theme_park"](area.searchArea);
#   relation["tourism"="artwork"](area.searchArea);
#   relation["tourism"="viewpoint"](area.searchArea);
#   relation["tourism"="picnic_site"](area.searchArea);
#   relation["tourism"="alpine_hut"](area.searchArea);
#   relation["tourism"="hotel"](area.searchArea);
#   relation["tourism"="guest_house"](area.searchArea);
#   relation["tourism"="hostel"](area.searchArea);
#   relation["tourism"="camp_site"](area.searchArea);
#   relation["tourism"="caravan_site"](area.searchArea);
#   // You can add more tourism keys as needed.
  
#   // --- Historic-related features ---
#   relation["historic"](area.searchArea);
#   relation["historic"="monument"](area.searchArea);
#   relation["historic"="castle"](area.searchArea);
#   relation["historic"="ruins"](area.searchArea);
#   relation["historic"="archaeological_site"](area.searchArea);
#   relation["historic"="memorial"](area.searchArea);
#   relation["historic"="ship"](area.searchArea);
#   relation["historic"="citywalls"](area.searchArea);
#   relation["historic"="fort"](area.searchArea);
#   relation["historic"="railway"](area.searchArea);
#   relation["historic"="battlefield"](area.searchArea);
#   relation["historic"="chapel"](area.searchArea);
#   relation["historic"="cemetery"](area.searchArea);
#   relation["historic"="ruin"](area.searchArea);
#   relation["historic"="stupa"](area.searchArea);
#   relation["historic"="villa"](area.searchArea);
#   relation["historic"="synagogue"](area.searchArea);
#   relation["historic"="mosque"](area.searchArea);
#   relation["historic"="church"](area.searchArea);
#   relation["historic"="temple"](area.searchArea);
#   relation["historic"="minaret"](area.searchArea);
#   relation["historic"="windmill"](area.searchArea);
#   relation["historic"="farm"](area.searchArea);
#   relation["historic"="farmhouse"](area.searchArea);
#   relation["historic"="lavatory"](area.searchArea);
  
#   // --- Leisure-related features ---
#   relation["leisure"="park"](area.searchArea);
#   relation["leisure"="garden"](area.searchArea);
#   relation["leisure"="stadium"](area.searchArea);
#   relation["leisure"="sports_centre"](area.searchArea);
#   relation["leisure"="water_park"](area.searchArea);
#   relation["leisure"="pitch"](area.searchArea);
#   relation["leisure"="fitness_station"](area.searchArea);
#   relation["leisure"="swimming_pool"](area.searchArea);
#   relation["leisure"="playground"](area.searchArea);
#   relation["leisure"="bandstand"](area.searchArea);
#   relation["leisure"="marina"](area.searchArea);
#   relation["leisure"="playcentre"](area.searchArea);
#   relation["leisure"="nature_reserve"](area.searchArea);
  
#   // --- Amenity-related features ---
#   relation["amenity"="cafe"](area.searchArea);
#   relation["amenity"="restaurant"](area.searchArea);
#   relation["amenity"="pub"](area.searchArea);
#   relation["amenity"="bar"](area.searchArea);
#   relation["amenity"="fast_food"](area.searchArea);
#   relation["amenity"="theatre"](area.searchArea);
#   relation["amenity"="cinema"](area.searchArea);
#   relation["amenity"="ice_cream"](area.searchArea);
#   relation["amenity"="bank"](area.searchArea);
#   relation["amenity"="clinic"](area.searchArea);
#   relation["amenity"="hospital"](area.searchArea);
#   relation["amenity"="pharmacy"](area.searchArea);
#   relation["amenity"="bicycle_rental"](area.searchArea);
#   relation["amenity"="bicycle_parking"](area.searchArea);
#   relation["amenity"="car_rental"](area.searchArea);
#   relation["amenity"="car_sharing"](area.searchArea);
#   relation["amenity"="parking"](area.searchArea);
#   relation["amenity"="toilets"](area.searchArea);
#   relation["amenity"="shelter"](area.searchArea);
#   relation["amenity"="shower"](area.searchArea);
#   relation["amenity"="drinking_water"](area.searchArea);
#   relation["amenity"="waste_basket"](area.searchArea);
#   relation["amenity"="place_of_worship"](area.searchArea);
#   relation["amenity"="marketplace"](area.searchArea);
#   relation["amenity"="library"](area.searchArea);
#   relation["amenity"="community_centre"](area.searchArea);
#   relation["amenity"="police"](area.searchArea);
#   relation["amenity"="fire_station"](area.searchArea);
#   relation["amenity"="post_office"](area.searchArea);
#   relation["amenity"="bureau_de_change"](area.searchArea);
#   relation["amenity"="atm"](area.searchArea);
#   relation["amenity"="fountain"](area.searchArea);
#   relation["amenity"="bench"](area.searchArea);
#   relation["amenity"="biergarten"](area.searchArea);
#   relation["amenity"="embassy"](area.searchArea);
#   relation["amenity"="prison"](area.searchArea);
#   relation["amenity"="dojo"](area.searchArea);
#   relation["amenity"="casino"](area.searchArea);
#   relation["amenity"="conference_centre"](area.searchArea);
#   relation["amenity"="kindergarten"](area.searchArea);
#   relation["amenity"="school"](area.searchArea);
#   relation["amenity"="college"](area.searchArea);
#   relation["amenity"="university"](area.searchArea);
#   relation["amenity"="post_box"](area.searchArea);
#   relation["amenity"="shrine"](area.searchArea);
#   relation["amenity"="water_point"](area.searchArea);
#   relation["amenity"="waste_disposal"](area.searchArea);
#   relation["amenity"="social_facility"](area.searchArea);
#   relation["amenity"="veterinary"](area.searchArea);
  
#   // --- Natural features ---
#   relation["natural"="water"](area.searchArea);
#   relation["natural"="wood"](area.searchArea);
#   relation["natural"="peak"](area.searchArea);
#   relation["natural"="cave"](area.searchArea);
#   relation["natural"="cliff"](area.searchArea);
#   relation["natural"="spring"](area.searchArea);
#   relation["natural"="tree_row"](area.searchArea);
#   relation["natural"="bay"](area.searchArea);
#   relation["natural"="beach"](area.searchArea);
#   relation["natural"="coastline"](area.searchArea);
#   relation["natural"="desert"](area.searchArea);
#   relation["natural"="grassland"](area.searchArea);
#   relation["natural"="heath"](area.searchArea);
#   relation["natural"="moor"](area.searchArea);
#   relation["natural"="scrub"](area.searchArea);
#   relation["natural"="scree"](area.searchArea);
#   relation["natural"="wetland"](area.searchArea);
  
#   // --- Shop-related features ---
#   relation["shop"="souvenir"](area.searchArea);
#   relation["shop"="antique"](area.searchArea);
#   relation["shop"="craft"](area.searchArea);
#   relation["shop"="art"](area.searchArea);
#   relation["shop"="clothes"](area.searchArea);
#   relation["shop"="shoes"](area.searchArea);
#   relation["shop"="jewelry"](area.searchArea);
#   relation["shop"="bakery"](area.searchArea);
#   relation["shop"="butcher"](area.searchArea);
#   relation["shop"="supermarket"](area.searchArea);
#   relation["shop"="convenience"](area.searchArea);
#   relation["shop"="electronics"](area.searchArea);
#   relation["shop"="furniture"](area.searchArea);
#   relation["shop"="hobby"](area.searchArea);
#   relation["shop"="sports"](area.searchArea);
#   relation["shop"="toys"](area.searchArea);
#   relation["shop"="books"](area.searchArea);
#   relation["shop"="music"](area.searchArea);
#   relation["shop"="florist"](area.searchArea);
#   relation["shop"="doityourself"](area.searchArea);
#   relation["shop"="car"](area.searchArea);
#   relation["shop"="bicycle"](area.searchArea);
#   relation["shop"="computer"](area.searchArea);
#   relation["shop"="pet"](area.searchArea);
#   relation["shop"="mall"](area.searchArea);
#   relation["shop"="mall"]["brand"="local"](area.searchArea);
  
#   // --- Man‑made & Other features ---
#   relation["man_made"="lighthouse"](area.searchArea);
#   relation["man_made"="obelisk"](area.searchArea);
#   relation["man_made"="mast"](area.searchArea);
#   relation["man_made"="tower"](area.searchArea);
  
#   // --- Craft, Sport, Office, Public Transport ---
#   relation["craft"="brewery"](area.searchArea);
#   relation["craft"="winery"](area.searchArea);
#   relation["sport"="ski"](area.searchArea);
#   relation["sport"="golf"](area.searchArea);
#   relation["sport"="surfing"](area.searchArea);
#   relation["office"="embassy"](area.searchArea);
#   relation["office"="tourist_info"](area.searchArea);
#   relation["public_transport"="station"](area.searchArea);
#   relation["public_transport"="stop_area"](area.searchArea);
  
#   // --- Administrative boundaries & waterways ---
#   relation["boundary"="administrative"](area.searchArea);
#   relation["waterway"="river"](area.searchArea);
#   relation["waterway"="canal"](area.searchArea);
# );
# out center;
# Overpass query for relations in Istanbul.
# 'out center' is used to attempt to get a central coordinate.


query = """
[out:json][timeout:120];
area["name"="İstanbul"]->.searchArea;
(
  relation["man_made"="lighthouse"](area.searchArea);
  relation["man_made"="obelisk"](area.searchArea);
  relation["man_made"="mast"](area.searchArea);
  relation["man_made"="tower"](area.searchArea);

  relation["craft"="brewery"](area.searchArea);
  relation["craft"="winery"](area.searchArea);
  relation["sport"="ski"](area.searchArea);
  relation["sport"="golf"](area.searchArea);
  relation["sport"="surfing"](area.searchArea);
  relation["office"="embassy"](area.searchArea);
  relation["office"="tourist_info"](area.searchArea);
  relation["public_transport"="station"](area.searchArea);
  relation["public_transport"="stop_area"](area.searchArea);
  
  relation["boundary"="administrative"](area.searchArea);
  relation["waterway"="river"](area.searchArea);
  relation["waterway"="canal"](area.searchArea);
);
out center;

"""

print("📡 Sending relations query to Overpass API...")
response = requests.get(url, params={"data": query})

if response.status_code == 200:
    data = response.json()
    places = []
    
    # Process each relation element (using its center if available)
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
    
    # Save the processed relations data to a JSON file
    with open("../../new_data/relations/others.json", "w", encoding="utf-8") as f:
        json.dump(places, f, ensure_ascii=False, indent=4)
    
    print("✅ Relations data extracted and saved to 'osm_istanbul_relations.json'.")
else:
    print("❌ API request failed with status code:", response.status_code)

