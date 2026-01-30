
import os
import time
import requests
import hashlib
import hmac
import base64
from dotenv import load_dotenv

load_dotenv()

# Copy of functions from naver_service.py to test in isolation

def get_related_keywords(keyword):
    try:
        url = "https://ac.search.naver.com/nx/ac"
        params = {
            "q": keyword,
            "con": "0",
            "frm": "nv",
            "ans": "2",
            "r_format": "json",
            "r_enc": "UTF-8",
            "r_unicode": "0",
            "t_koreng": "1",
            "run": "2",
            "rev": "4",
            "q_enc": "UTF-8",
            "st": "100"
        }
        res = requests.get(url, params=params)
        data = res.json()
        
        keywords = []
        items = data.get('items', [])
        for group in items:
            for item in group:
                keywords.append(item[0])
        
        keywords = list(dict.fromkeys(keywords))
        if keyword in keywords:
            keywords.remove(keyword)
            
        print(f"Autocomplete Keywords ({len(keywords)}): {keywords}")
        return keywords
    except Exception as e:
        print(f"Related keywords error: {e}")
        return []

def generate_signature(timestamp, method, uri, secret_key):
    message = f"{timestamp}.{method}.{uri}"
    signature = hmac.new(bytes(secret_key, "utf-8"), bytes(message, "utf-8"), hashlib.sha256).digest()
    return base64.b64encode(signature).decode("utf-8")

def get_bulk_search_volumes(keyword):
    try:
        license_key = os.getenv("NAVER_AD_ACCESS_LICENSE")
        secret_key = os.getenv("NAVER_AD_SECRET_KEY")
        customer_id = os.getenv("NAVER_AD_CUSTOMER_ID")
        
        print(f"Keys: License={bool(license_key)}, Secret={bool(secret_key)}, ID={customer_id}")
        
        if not license_key or not secret_key or not customer_id:
            print("Missing keys")
            return {}
            
        base_url = "https://api.naver.com"
        uri = "/keywordstool"
        method = "GET"
        timestamp = str(int(time.time() * 1000))
        
        signature = generate_signature(timestamp, method, uri, secret_key)
        
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "X-Timestamp": timestamp,
            "X-API-KEY": license_key,
            "X-Customer": customer_id, 
            "X-Signature": signature
        }
        
        params = {
            "hintKeywords": keyword.replace(" ", ""),
            "showDetail": "1"
        }
        
        print(f"Requesting Ad API for hint: {params['hintKeywords']}")
        res = requests.get(base_url + uri, params=params, headers=headers)
        
        if res.status_code == 200:
            data = res.json()
            keyword_list = data.get('keywordList', [])
            print(f"Ad API returned {len(keyword_list)} keywords.")
            
            result = {}
            # Print first 5 for sample
            for item in keyword_list[:5]:
                print(f" - API Item: {item['relKeyword']} (PC: {item.get('monthlyPcQcCnt')})")

            for item in keyword_list:
                kwd = item['relKeyword']
                pc_vol = item.get('monthlyPcQcCnt', 0)
                mo_vol = item.get('monthlyMobileQcCnt', 0)
                
                if isinstance(pc_vol, str): pc_vol = 0
                if isinstance(mo_vol, str): mo_vol = 0
                
                result[kwd.replace(" ", "")] = {
                    'original_keyword': kwd,
                    'pc': pc_vol,
                    'mobile': mo_vol,
                    'total': pc_vol + mo_vol
                }
            return result
        else:
            print(f"Ad API Error: {res.status_code} {res.text}")
            return {}
            
    except Exception as e:
        print(f"Bulk search volume error: {e}")
        return {}

if __name__ == "__main__":
    test_kwd = "강남 맛집"
    print(f"Testing with '{test_kwd}'...")
    
    # 1. Get targets
    targets = get_related_keywords(test_kwd)
    
    # 2. Get data
    ad_data = get_bulk_search_volumes(test_kwd)
    
    # 3. Match
    matched_count = 0
    for t in targets:
        key = t.replace(" ", "")
        if key in ad_data:
            matched_count += 1
            print(f"[MATCH] {t}: {ad_data[key]}")
        else:
            print(f"[MISS] {t} (Key: {key})")
            
    print(f"\nTotal Targets: {len(targets)}, Matched: {matched_count}")
