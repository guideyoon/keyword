
import requests
from bs4 import BeautifulSoup
import json
import time

def get_datalab_shopping_keywords():
    # Naver DataLab Shopping Insight Home (shows top keywords by category)
    # The actual data is loaded via API or embedded in JS.
    # Let's check the main page or the category page.
    
    url = "https://datalab.naver.com/shoppingInsight/sCategory.naver"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    
    # Actually, DataLab uses an internal API: https://datalab.naver.com/shoppingInsight/getCategoryKeywordRank.naver
    # Let's try to hit that.
    
    api_url = "https://datalab.naver.com/shoppingInsight/getCategoryKeywordRank.naver"
    
    # We need category IDs.
    # Fashion: 50000000
    # Cosmetics: 50000002
    # Digital: 50000003
    # Food: 50000006
    
    cids = [
        {"cid": "50000000", "name": "패션의류"},
        {"cid": "50000003", "name": "디지털/가전"},
        {"cid": "50000006", "name": "식품"}
    ]
    
    results = {}
    
    for c in cids:
        data = {
            "cid": c['cid'],
            "timeUnit": "date",
            "startDate": "2023-12-01", # Should be recent, maybe they auto-adjust? Let's try omit or fixed.
            "endDate": "2023-12-13",
            "age": "",
            "gender": "",
            "device": "",
            "page": 1,
            "count": 20
        }
        # Actually they use POST with form data usually.
        # Let's try scraping the HTML of the main page if API is protected (often requires specific headers/cookies).
        
        try:
            # First try just GETting the page to see if keywords are rendered server-side (unlikely for DataLab).
            # If SPA, we need headers.
            # Let's try the POST API with standard headers.
            
            headers['Referer'] = url
            headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            
            # Use requests.post
            # DataLab requires valid dates. 
            # If I don't know today, I might fail.
            # But let's try a simple scraping of "Best 100" if available elsewhere.
            # The URL `https://search.shopping.naver.com/best/home` is better!
            pass
        except:
            pass

    # Plan B: Shopping Best (Rank)
    # https://search.shopping.naver.com/best/category/click
    # This is much easier to scrape.
    
    best_url = "https://search.shopping.naver.com/best/home"
    try:
        res = requests.get(best_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Determine selector for items
        # Usually .chartList_item_text__...
        # We need to print snippet to find classes.
        
        # print(res.text[:1000]) # debug
        
        # Search for any product names
        items = soup.select("div[class*='chartList_item_text']")
        print(f"Found {len(items)} items in Best Home")
        
        keywords = []
        for item in items:
            title = item.find(text=True, recursive=True)
            if title:
                print(title)
                keywords.append(title)
                
        return keywords[:20]

    except Exception as e:
        print("Error:", e)
        return []

if __name__ == "__main__":
    get_datalab_shopping_keywords()
