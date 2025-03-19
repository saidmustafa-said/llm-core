import requests
import json

# Overpass API endpoint
url = "https://overpass-api.de/api/interpreter"

# Overpass query to get nodes with tags in Istanbul
query = """
[out:json][timeout:60];
area["name"="İstanbul"]->.searchArea;
(
  node(area.searchArea);
);
out body;
"""

# List of tags you're interested in
selected_tags = ["amenity", "tourism",
                 "shop", "leisure", "historic", "natural", "sport"]


def extract_tag_values(data, selected_tags):
    """
    Extracts the unique values for each tag in selected_tags from the dataset.
    Returns a dictionary mapping each tag to a set of its unique values.
    """
    tag_values = {tag: set() for tag in selected_tags}
    for item in data:
        tags = item.get("tags", {})
        for tag in selected_tags:
            if tag in tags:
                tag_values[tag].add(tags[tag])
    return tag_values


# Sending the query to the Overpass API
print("📡 Sending request to Overpass API to extract data...")
response = requests.get(url, params={"data": query})

if response.status_code == 200:
    data = response.json()
    print("✅ Data received successfully.")

    # Extract elements (nodes with tags)
    elements = data.get("elements", [])

    # Extract unique values for each of the selected tags
    tag_values = extract_tag_values(elements, selected_tags)

    # Convert sets to lists so they can be saved in JSON format
    tag_values_json = {tag: list(values) for tag, values in tag_values.items()}

    # Save the tag values to a file
    with open('../data/selected_tag_values.json', 'w', encoding='utf-8') as file:
        json.dump(tag_values_json, file, ensure_ascii=False, indent=4)

    print("📂 Tag values saved to selected_tag_values.json.")
else:
    print("❌ API request failed with status code:", response.status_code)
