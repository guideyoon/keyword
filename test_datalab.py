
from naver_service import get_api_keys
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_datalab_shopping():
    # Naver DataLab Shopping Insight API
    # https://developers.naver.com/docs/serviceapi/datalab/shopping/shopping.md
    
    url = "https://openapi.naver.com/v1/datalab/shopping/categories"
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    
    if not client_id:
        print("No keys")
        return

    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "Content-Type": "application/json"
    }
    
    # Body: Request trend for major categories
    # 50000000 -> Digital/Home Appliance
    # 50000002 -> Cosmetics/Beauty
    body = {
        "startDate": "2023-01-01",
        "endDate": "2023-12-01",
        "timeUnit": "month",
        "category": [
            {"name": "패션의류", "param": ["50000000"]},
            {"name": "화장품", "param": ["50000002"]}
        ]
    }
    # Note: This API returns 'Ratio', not actual keywords.
    # The user wants "KEYWORDS".
    # https://developers.naver.com/docs/serviceapi/datalab/search/search.md -> Also Ratio.
    
    # Is there an API for "Top Shopping Keywords"?
    # Officially, Naver provides 'Shopping Insight' on the site, but API is limited to ratios given specific keywords.
    
    # Strategy C: Scrape `https://datalab.naver.com/shoppingInsight/sCategory.naver`
    # This page shows "Popular Search Terms" by Category.
    
    print("API Check: DataLab only returns trends for GIVEN keywords/categories, not extracting NEW keywords.")
    print("Switching to checking feasibility of scraping DataLab popular terms.")

if __name__ == "__main__":
    test_datalab_shopping()
