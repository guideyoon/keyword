import os
from concurrent.futures import ThreadPoolExecutor
from naver_service import get_keyword_info
from dotenv import load_dotenv

load_dotenv()

def test_parallel():
    keywords = ["서울전시회", "리퍼브매장", "파주가볼만한곳", "MBTI테스트", "MBTI검사", "리퍼노트북", "인기아이템"]
    
    def fetch(k):
        res = get_keyword_info(k)
        return k, res
    
    print("Starting parallel test...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch, keywords))
        
    for k, res in results:
        print(f"Keyword: {k} | Result: {res}")

if __name__ == "__main__":
    test_parallel()
