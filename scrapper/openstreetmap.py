import requests
import json

url = "https://overpass-api.de/api/interpreter"

query = """
[out:json];
area["name"="İstanbul"]->.searchArea;  // Search for Istanbul
(
  node["tourism"="attraction"](area.searchArea);  // Tourist attractions
  node["tourism"="museum"](area.searchArea);      // Museums
  node["tourism"="theme_park"](area.searchArea);  // Theme parks
  node["tourism"="water_park"](area.searchArea); // Water parks
  node["tourism"="aquarium"](area.searchArea);   // Aquariums
  node["historic"](area.searchArea);           // Historical places (general)
  node["historic"="archaeological_site"](area.searchArea); // Archaeological sites
  node["historic"="monument"](area.searchArea); // Monuments
  node["historic"="memorial"](area.searchArea); // Memorials
  node["historic"="castle"](area.searchArea);  // Castles
  node["historic"="ruins"](area.searchArea);   // Ruins
  node["leisure"="park"](area.searchArea);      // Parks (general leisure)
  node["leisure"="garden"](area.searchArea);    // Gardens
  node["leisure"="playground"](area.searchArea); // Playgrounds
  node["leisure"="dog_park"](area.searchArea);  // Dog parks
  node["amenity"="beach"](area.searchArea);      // Beaches
  node["amenity"="nightclub"](area.searchArea);  // Nightclubs
  node["amenity"="bar"](area.searchArea);        // Bars
  node["amenity"="pub"](area.searchArea);        // Pubs
  node["amenity"="cafe"](area.searchArea);       // Cafes
  node["amenity"="restaurant"](area.searchArea); // Restaurants
  node["amenity"="fast_food"](area.searchArea);  // Fast food
  node["amenity"="shopping_centre"](area.searchArea); // Shopping malls/centers
  node["shop"="mall"](area.searchArea);        // Shopping malls (alternate tag)
  node["amenity"="cinema"](area.searchArea);     // Cinemas
  node["amenity"="theatre"](area.searchArea);    // Theatres
  node["amenity"="arts_centre"](area.searchArea); // Arts centers
  node["amenity"="community_centre"](area.searchArea); // Community centers
  node["sport"="beachvolleyball"](area.searchArea); // Beach volleyball areas
  node["sport"="swimming"](area.searchArea);      // Swimming pools/beaches
  node["natural"="beach"](area.searchArea);    // Natural beaches
);
out body;
"""

response = requests.get(url, params={"data": query})

if response.status_code == 200:
    data = response.json()

    places = []
    for element in data.get("elements", []):
        if "lat" in element and "lon" in element:
            tags = element.get("tags", {})
            name = tags.get("name", tags.get("official_name", "Bilinmeyen Yer"))
            description = tags.get("description", tags.get("wikipedia", "Açıklama yok"))
            category = tags.get("tourism", tags.get("historic", tags.get("amenity", "Diğer")))
            location = "Türkiye/İstanbul" 
            coordinates = {
                "latitude": element["lat"],
                "longitude": element["lon"]
            }
            places.append({
                "name": name,
                "description": description,
                "category": category,
                "location": location,
                "coordinates": coordinates
            })

    with open("../data/osm_istanbul.json", "w", encoding="utf-8") as f:
        json.dump(places, f, ensure_ascii=False, indent=4)
    with open("../data/raw.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


    print("✅ İstanbul'daki turistik yerler başarıyla kaydedildi!")
else:
    print("❌ API isteği başarısız oldu! Hata kodu:", response.status_code)
    try:
        error_message = response.json()
        print("Hata mesajı:", error_message)
    except json.JSONDecodeError:
        print("Hata mesajı alınamadı.")