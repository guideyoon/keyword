import requests
from bs4 import BeautifulSoup
import urllib.parse
import re

def get_monthly_blog_count_v2(keyword):
    encoded_kwd = urllib.parse.quote(keyword)
    # Simplified URL often used for scraping
    url = f"https://search.naver.com/search.naver?where=blog&query={encoded_kwd}&nso=so:r,p:1m,a:all"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Possible locations for total count
        # 1. .api_txt_lines.total_area (New PC/Mobile UI)
        # 2. .sub_txt (Older PC UI)
        # 3. .title_num (Common)
        # 4. Look for the pattern "1-10 / 1,234건"
        
        selectors = [".title_num", ".api_txt_lines.total_area", ".sub_txt", ".total_area"]
        for sel in selectors:
            target = soup.select_one(sel)
            if target:
                text = target.get_text()
                print(f"DEBUG: Found text '{text}' with selector '{sel}'")
                match = re.search(r'([\d,]+)건', text)
                if match:
                    return int(match.group(1).replace(',', ''))
        
        # Regex search in whole text as fallback
        match = re.search(r'/?\s*([\d,]+)건', soup.get_text())
        if match:
            print(f"DEBUG: Found count via global regex: {match.group(1)}")
            return int(match.group(1).replace(',', ''))
            
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 0

if __name__ == "__main__":
    kwd = "UFC"
    print(f"UFC: {get_monthly_blog_count_v2(kwd)}")
    kwd2 = "서울전시회"
    print(f"서울전시회: {get_monthly_blog_count_v2(kwd2)}")
