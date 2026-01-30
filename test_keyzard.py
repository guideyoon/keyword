
import requests
from bs4 import BeautifulSoup

def test_keyzard():
    url = "https://keyzard.org/realtime"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        
        if "구글" in response.text or "Google" in response.text:
            print("Found Google text in Keyzard")
            
        soup = BeautifulSoup(response.text, 'html.parser')
        # Keyzard usually has different columns.
        # Let's try to find any list.
        tables = soup.select("table")
        print(f"Found {len(tables)} tables.")
        
        for table in tables:
             # Just dump first row
             print(table.select_one("tr").get_text())
             
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_keyzard()
