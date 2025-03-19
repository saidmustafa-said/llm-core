import requests
import json
import os


def fetch_and_save_data(sitetype, amenity):
    # Overpass API endpoint
    url = "https://overpass-api.de/api/interpreter"

    # Overpass query
    query = f"""
    [out:json][timeout:60];
    area["name"="İstanbul"]->.searchArea;
    (
      node[{sitetype}={amenity}](area.searchArea);
    );
    out body;
    """

    print(f"📡 Sending {amenity} query to Overpass API...")
    response = requests.get(url, params={"data": query})

    if response.status_code == 200:
        data = response.json()
        print("✅ Data received successfully.")

        # Extracting the list of elements from the response
        elements = data.get("elements", [])

        # Prepare the transformed data list
        transformed_data = []

        # Create a set to keep track of seen locations (latitude and longitude pairs)
        seen_locations = set()

        for element in elements:
            # Get description and note, merge them if both exist
            description = element.get("tags", {}).get("description", None)
            note = element.get("tags", {}).get("note", None)

            # Combine description and note
            additional_info = ""
            if description:
                additional_info += description
            if note:
                if additional_info:  # Add space if both description and note exist
                    additional_info += " "
                additional_info += note

            # Build the schema for each element
            node_data = {
                "lat": element.get("lat", 0),
                "lon": element.get("lon", 0),
                "tags": {
                    "addr:city": element.get("tags", {}).get("addr:city", "İstanbul"),
                    "addr:district": element.get("tags", {}).get("addr:district", None),
                    "description": additional_info,
                    "opening_hours": element.get("tags", {}).get("opening_hours", None),
                    "phone": element.get("tags", {}).get("phone", None),
                    "branch": element.get("tags", {}).get("branch", None),
                    "amenity": element.get("tags", {}).get("amenity", amenity),
                    "mobile": element.get("tags", {}).get("mobile", None),
                    "addr:street": element.get("tags", {}).get("addr:street", None),
                    "cuisine": element.get("tags", {}).get("cuisine", None),
                    # Add language-specific names (with None as placeholders if missing)
                    "name": element.get("tags", {}).get("name", None),
                    "name:en": element.get("tags", {}).get("name:en", None),
                    "name:uk": element.get("tags", {}).get("name:uk", None),
                    "name:de": element.get("tags", {}).get("name:de", None),
                    "name:tr": element.get("tags", {}).get("name:tr", None),
                    "name:ru": element.get("tags", {}).get("name:ru", None),
                    "name:ar": element.get("tags", {}).get("name:ar", None)
                }
            }

            # Check if the location (lat, lon) is already in the seen locations set
            location = (node_data['lat'], node_data['lon'])
            if location not in seen_locations:
                # If it's a new location, add it to the set and append to the transformed data
                seen_locations.add(location)
                transformed_data.append(node_data)
            else:
                # Print a message if it's a duplicate
                print(
                    f"⚠️ Duplicate found at lat: {node_data['lat']}, lon: {node_data['lon']}")

        # Create folder path if it doesn't exist
        folder_path = f'data_process/data_store/new_data/{sitetype}'
        # Create the folder if it doesn't exist
        os.makedirs(folder_path, exist_ok=True)

        # Saving the transformed data to a file
        with open(f'{folder_path}/{amenity}.json', 'w', encoding='utf-8') as file:
            json.dump(transformed_data, file, ensure_ascii=False, indent=4)
        print(f"📂 Data saved to {amenity}.json.")
    else:
        print(f"❌ API request failed with status code: {response.status_code}")


def process_queries(json_file):
    # Read the JSON file
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Iterate over the dictionary
    for sitetype, amenities in data.items():
        for amenity in amenities:
            fetch_and_save_data(sitetype, amenity)


# Path to the JSON file
json_file_path = "data_process/data_collection/data/selected_tag.json"

# Process queries
process_queries(json_file_path)
