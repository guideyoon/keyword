
import requests
import json
from datetime import datetime, timedelta

def test_datalab_rank_api():
    url = "https://datalab.naver.com/shoppingInsight/getCategoryKeywordRank.naver"
    
    # Headers are critical for internal APIs
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Referer": "https://datalab.naver.com/shoppingInsight/sCategory.naver",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://datalab.naver.com"
    }

    # Date handling: Needs to be recent. 2 days ago is safe.
    # Format: YYYY-MM-DD
    # But usually DataLab has a 1-day lag.
    today = datetime.now()
    end_date = (today - timedelta(days=2)).strftime("%Y-%m-%d")
    start_date = (today - timedelta(days=3)).strftime("%Y-%m-%d")
    
    # Payload
    # cid: 50000000 (Fashion)
    data = {
        "cid": "50000000",
        "timeUnit": "date",
        "startDate": start_date,
        "endDate": end_date,
        "age": "",
        "gender": "",
        "device": "",
        "page": 1,
        "count": 20
    }
    
    print(f"Requesting DataLab Rank for {start_date} ~ {end_date}...")
    
    try:
        res = requests.post(url, headers=headers, data=data)
        if res.status_code == 200:
            result = res.json()
            # Structure: ranks: [{rank, keyword}, ...]
            print("Success!")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"Failed: {res.status_code}")
            print(res.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_datalab_rank_api()
