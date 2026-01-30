import requests
import json

def test_ac(keyword):
    url = f"https://ac.search.naver.com/nx/ac"
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
    
    print(f"Fetching Autocomplete for {keyword}")
    res = requests.get(url, params=params)
    data = res.json()
    
    # print(json.dumps(data, indent=2, ensure_ascii=False))
    
    items = data.get('items', [])
    if items:
        print("Found items:")
        for group in items:
            for item in group:
                print(f" - {item[0]}")
    else:
        print("No items found.")

if __name__ == "__main__":
    test_ac("제습기 추천")
