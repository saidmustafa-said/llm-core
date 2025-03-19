import requests
import json
from collections import Counter

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


def find_frequent_tag_keys(data, min_count=50):
    """
    Analyzes the data to count how many times each tag key appears,
    and returns a dictionary of tag keys with counts greater than or equal to min_count.
    """
    tag_counter = Counter()
    for item in data:
        tags = item.get("tags", {})
        tag_counter.update(tags.keys())

    # Filter and return tag keys that occur at least min_count times
    frequent_tags = {tag: count for tag,
                     count in tag_counter.items() if count >= min_count}
    return frequent_tags


# Sending the query to the Overpass API
print("📡 Sending request to Overpass API to extract data...")
response = requests.get(url, params={"data": query})

if response.status_code == 200:
    data = response.json()
    print("✅ Data received successfully.")

    # Extracting the elements (nodes with tags)
    elements = data.get("elements", [])

    # Analyze the frequency of tag keys (you can adjust min_count as needed)
    frequent_tags = find_frequent_tag_keys(elements, min_count=100)

    # Save the frequent tag keys to a file
    with open('../data/unique_frequent_tag_keys.json', 'w', encoding='utf-8') as file:
        json.dump(frequent_tags, file, ensure_ascii=False, indent=4)
    print("📂 Frequent tag keys saved to unique_frequent_tag_keys.json.")
else:
    print("❌ API request failed with status code:", response.status_code)
