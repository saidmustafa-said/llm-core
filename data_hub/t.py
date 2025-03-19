import requests

APIS = {
    "nominatim": {
        "url": "https://nominatim.openstreetmap.org/reverse",
        "params": lambda lat, lon: {"format": "json", "lat": lat, "lon": lon},
    },
    "geocode_maps": {
        "url": "https://geocode.maps.co/reverse",
        "params": lambda lat, lon: {"lat": lat, "lon": lon},
    },
}


def extract_address(data):
    """
    Extracts and formats the most relevant address information
    from the geocoding response.
    """
    if 'display_name' in data:
        print("1: ", data['display_name'])
        return data['display_name']
    if 'address' in data:
        address = data['address']
        print("2: ", address)
        components = [
            address.get('road', ''),
            address.get('suburb', ''),
            address.get('city', ''),
            address.get('county', ''),
            address.get('state', ''),
            address.get('country', '')
        ]
        # Remove empty components
        return ", ".join([component for component in components if component])
    if 'city' in data and 'countryName' in data:
        print(f"3: {data.get('city', '')}, {data.get('countryName', '')}")
        return f"{data.get('city', '')}, {data.get('countryName', '')}"
    return "Address Not Found"


def test_api(api_name, lat, lon):
    api = APIS[api_name]

    # Add a free User-Agent for Nominatim to avoid 403 error
    headers = {"User-Agent": "MyApp/1.0 (sayedmustafa707@gmail.com)"}

    try:
        # For Nominatim API, add headers, for others, no need for User-Agent
        if api_name == "nominatim":
            response = requests.get(
                api["url"], params=api["params"](lat, lon), headers=headers, timeout=5)
        else:
            response = requests.get(
                api["url"], params=api["params"](lat, lon), timeout=5)

        if response.status_code == 200:
            data = response.json()
            address = extract_address(data)
            return f"{api_name}: {address}"
        return f"{api_name}: Error {response.status_code}"
    except Exception as e:
        return f"{api_name}: Exception {str(e)}"


def main():
    lat, lon = 41.0336104, 28.9785641   # Example coordinates (New York City)
    for api_name in APIS.keys():
        result = test_api(api_name, lat, lon)
        print(result)


if __name__ == "__main__":
    main()
