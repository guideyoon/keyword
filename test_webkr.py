
from naver_service import get_api_keys
import requests
import json

def test_webkr():
    client_id, client_secret = get_api_keys()
    url = "https://openapi.naver.com/v1/search/webkr?query=테스트&display=2"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    res = requests.get(url, headers=headers)
    print(json.dumps(res.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_webkr()
