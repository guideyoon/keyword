
from naver_service import get_datalab_shopping_trends, get_search_volumes_for_keywords, get_keyword_info

def verify_shopping_trends():
    print("1. Fetching DataLab Trends (Fashion - 50000000)...")
    trends = get_datalab_shopping_trends("50000000")
    
    if not trends:
        print("Failed to fetch trends.")
        return

    print(f"Fetched {len(trends)} keywords.")
    print(f"Top 3: {[t['keyword'] for t in trends[:3]]}")
    
    # Check Volume Fetching
    keywords = [t['keyword'] for t in trends[:5]]
    print(f"\n2. Fetching Volume for top 5: {keywords}")
    vols = get_search_volumes_for_keywords(keywords)
    print(f"Volume Results: {vols}")
    
    # Check Doc Counts
    print("\n3. Checking Doc Counts...")
    for k in keywords:
        info = get_keyword_info(k)
        print(f" - {k}: {info.get('total', 0)} docs")

if __name__ == "__main__":
    verify_shopping_trends()
