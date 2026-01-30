from naver_service import search_blog
import os
from dotenv import load_dotenv

load_dotenv()

def test_api():
    print("Testing Naver API Credentials...")
    client_id = os.getenv("NAVER_CLIENT_ID", "").strip()
    client_secret = os.getenv("NAVER_CLIENT_SECRET", "").strip()
    
    print(f"Loaded Client ID: {client_id[:4]}****{client_id[-4:] if len(client_id)>4 else ''}")
    print(f"Loaded Secret: {client_secret[:2]}****{client_secret[-2:] if len(client_secret)>2 else ''}")
    
    if not client_id or not client_secret:
        print("ERROR: Keys are empty.")
        return

    result = search_blog("test")
    
    if "error" in result:
        print(f"FAILED: {result['error']}")
        if "details" in result:
            print(f"Details: {result['details']}")
    else:
        print("SUCCESS! API Key is working.")
        print(f"Found {result.get('total')} items.")

if __name__ == "__main__":
    test_api()
