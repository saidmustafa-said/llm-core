import requests
from bs4 import BeautifulSoup
import json

URL = "https://en.wikipedia.org/wiki/Lists_of_tourist_attractions"
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(URL, headers=headers)

soup = BeautifulSoup(response.text, "html.parser")

places = []
for item in soup.select("div.mw-parser-output ul li a"):
    name = item.text.strip()
    link = "https://en.wikipedia.org" + item["href"] if item.has_attr("href") else None

    place = {
        "name": name,
        "description": "Wikipedia'da daha fazla bilgi var.",
        "location": "Bilinmiyor",
        "coordinates": {"latitude": None, "longitude": None},
        "wiki_url": link
    }
    places.append(place)

with open("data/wikipedia.json", "w", encoding="utf-8") as f:
    json.dump(places, f, ensure_ascii=False, indent=4)

print("✅ JSON dosyası başarıyla oluşturuldu! 🎉")
