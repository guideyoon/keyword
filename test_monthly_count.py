import requests
from bs4 import BeautifulSoup
import urllib.parse

def get_monthly_blog_count(keyword):
    # nso=so:r,p:1m,a:all means: Sort by relevance (r), period 1 month (1m), all regions (all)
    encoded_kwd = urllib.parse.quote(keyword)
    url = f"https://search.naver.com/search.naver?query={encoded_kwd}&nso=so:r,p:1m,a:all&where=blog"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        with open("naver_search_debug.html", "w", encoding="utf-8") as f:
            f.write(res.text)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # In current Naver UI, total count is often in .title_num or .api_txt_lines.total_area
        # Look for "건" or "1-10 / 1,234건"
        total_text = ""
        
        # New UI: .api_txt_lines.total_area
        # Old UI: .title_num
        target = soup.select_one(".title_num") or soup.select_one(".api_txt_lines.total_area")
        
        if target:
            total_text = target.get_text()
            print(f"DEBUG: Raw text for {keyword}: {total_text}")
            # Extract numbers from "1,234건" or "약 1,234건" or "1 / 1,234건"
            import re
            match = re.search(r'/ ([\d,]+)건', total_text) or re.search(r'([\d,]+)건', total_text)
            if match:
                count_str = match.group(1).replace(',', '')
                return int(count_str)
        
        # Fallback for mobile or different UI
        # Check if there's a script with total results
        return 0
    except Exception as e:
        print(f"Error scraping monthly count for {keyword}: {e}")
        return 0

if __name__ == "__main__":
    kwd = "UFC"
    count = get_monthly_blog_count(kwd)
    print(f"Monthly Blog Count for '{kwd}': {count}")
    
    kwd2 = "서울전시회"
    count2 = get_monthly_blog_count(kwd2)
    print(f"Monthly Blog Count for '{kwd2}': {count2}")
