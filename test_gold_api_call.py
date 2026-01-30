import requests
import json
import sys

def test_gold():
    kwd = sys.argv[1] if len(sys.argv) > 1 else "노트북"
    url = f"http://localhost:5000/api/gold/discover?q={kwd}"
    try:
        print(f"Testing {url}...")
        response = requests.get(url, timeout=20)
        print(f"Status Code: {response.status_code}")
        try:
            results = response.json()
            print(f"Response JSON (Found {len(results)} items):")
            print(json.dumps(results[:5], indent=2, ensure_ascii=False))
        except:
            print("Response text (Not JSON):")
            print(response.text[:500])
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_gold()
