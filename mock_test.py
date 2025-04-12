import requests
import json

BASE_URL = "http://127.0.0.1:8000"
USER_ID = "said1"
LATITUDE = 40.971255
LONGITUDE = 28.793878
SEARCH_RADIUS = 1000
NUM_CANDIDATES = 2

# Step 1: Create a session
session_response = requests.post(
    f"{BASE_URL}/session", json={"user_id": USER_ID})
session_data = session_response.json()
session_id = session_data.get("session_id")

print(f"\n🟢 Session ID: {session_id}\n")
print("=" * 60)

# Step 2: Message list
messages = [
    "is there a cafe close by",
    "can you find me a restaurant close to the BELTUR mini",
    "is there a description for Görkem Kilis Sofrası"
]

# Step 3: Send messages
for i, msg in enumerate(messages, start=1):
    payload = {
        "user_id": USER_ID,
        "session_id": session_id,
        "message": msg,
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "search_radius": SEARCH_RADIUS,
        "num_candidates": NUM_CANDIDATES
    }
    response = requests.post(f"{BASE_URL}/message", json=payload)
    print(f"📨 Message {i}: {msg}")
    print("🧾 Response:")
    print(json.dumps(response.json(), indent=4, ensure_ascii=False))
    print("=" * 60)

# Step 4: Get session history
history_url = f"{BASE_URL}/session/{USER_ID}/{session_id}/history"
history_response = requests.get(history_url)
print("=" * 60)
print(f"\n📚 Session History ({history_url}):")
print(json.dumps(history_response.json(), indent=4, ensure_ascii=False))

# Step 5: Get session messages
messages_url = f"{BASE_URL}/session/{USER_ID}/{session_id}/messages"
messages_response = requests.get(messages_url)

print("=" * 60)
print(f"\n📩 Session Messages ({messages_url}):")
print(json.dumps(messages_response.json(), indent=4, ensure_ascii=False))
