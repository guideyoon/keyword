
import requests
from bs4 import BeautifulSoup

def inspect_signal():
    url = "https://signal.bz/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for text "Google" or "구글"
        if "구글" in response.text or "Google" in response.text:
            print("Found Google related text!")
            
        # Dump all text in potential trend containers
        # Usually .rank-layer or similar
        print(response.text[:1000])
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_signal()
