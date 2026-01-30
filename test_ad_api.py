import os
import time
import hmac
import hashlib
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("NAVER_AD_ACCESS_LICENSE")
SECRET_KEY = os.getenv("NAVER_AD_SECRET_KEY")

def generate_signature(timestamp, method, uri, secret_key):
    message = f"{timestamp}.{method}.{uri}"
    signature = hmac.new(bytes(secret_key, "utf-8"), bytes(message, "utf-8"), hashlib.sha256).digest()
    return base64.b64encode(signature).decode("utf-8")

def get_header(method, uri, api_key, secret_key):
    timestamp = str(int(time.time() * 1000))
    signature = generate_signature(timestamp, method, uri, secret_key)
    return {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Timestamp": timestamp,
        "X-API-KEY": api_key,
        "X-Customer": "123456", # Dummy customer ID, usually not needed for generic keyword tool?
        "X-Signature": signature
    }

def get_customer_id():
    # Attempt to find customer ID
    uri = "/advertiser/customer-info" # Common endpoint to check own info? Or /billing/customer
    # Actually for Search Ad API, we might simply list accounts: GET /advertiser-customers or /manager-customer
    # Let's try to find our own ID.
    
    # Actually, simpler: Many users just use their main account ID. 
    # Try listing methods if possible.
    
    # Try /billing/customer
    method = "GET"
    uri = "/billing/customer"
    
    timestamp = str(int(time.time() * 1000))
    signature = generate_signature(timestamp, method, uri, SECRET_KEY)
    
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Timestamp": timestamp,
        "X-API-KEY": API_KEY,
        "X-Signature": signature
    }
    
    try:
        print(f"Fetching Customer ID from {uri}...")
        res = requests.get("https://api.naver.com" + uri, headers=headers)
        if res.status_code == 200:
            data = res.json()
            # print(data)
            # usually returns list of customers
            # {"reservations": [...]} or just list
            return data
        else:
            print(f"Failed to get customer: {res.status_code} {res.text}")
            return None
    except Exception as e:
        print(f"Error getting customer: {e}")
        return None

if __name__ == "__main__":
    CUSTOMER_ID = os.getenv("NAVER_AD_CUSTOMER_ID")
    if not API_KEY or not SECRET_KEY or not CUSTOMER_ID:
        print("Keys missing")
    else:
        base_url = "https://api.naver.com"
        uri = "/keywordstool"
        method = "GET"
        
        timestamp = str(int(time.time() * 1000))
        signature = generate_signature(timestamp, method, uri, SECRET_KEY)
        
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "X-Timestamp": timestamp,
            "X-API-KEY": API_KEY,
            "X-Customer": CUSTOMER_ID, 
            "X-Signature": signature
        }
        
        params = {
            "hintKeywords": "한일가열식가습기",
            "showDetail": "1"
        }
        
        print(f"Testing Ad API for '한일가열식가습기' with Customer ID {CUSTOMER_ID}...")
        res = requests.get(base_url + uri, params=params, headers=headers)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            if 'keywordList' in data:
                print("Success! First result:")
                print(data['keywordList'][0])
            else:
                print("No keywordList found")
        else:
            print(f"Error Body: {res.text}")
