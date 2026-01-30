import requests
import json

def test_gold_discover():
    url = "http://127.0.0.1:5000/api/gold/discover?q=전시회"
    try:
        print(f"Calling {url}...")
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Found {len(data)} results.")
            if data:
                print("First result snippet:", json.dumps(data[0], indent=2, ensure_ascii=False))
        else:
            print(f"Error Body: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_gold_discover()
