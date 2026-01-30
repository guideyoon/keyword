import os
from naver_service import (
    get_related_keywords, 
    get_related_keywords_from_ad_api,
    get_search_volumes_for_keywords,
    get_keyword_info
)
from dotenv import load_dotenv

load_dotenv()

def debug_gold(seed):
    print(f"--- Debugging Golden Keyword Discovery for: {seed} ---")
    
    # 1. Sources
    scraped = get_related_keywords(seed)
    print(f"Scraped source: {len(scraped)} items")
    if scraped: print(f"  First 5: {scraped[:5]}")
    
    ad_related = get_related_keywords_from_ad_api(seed)
    print(f"Ad API source: {len(ad_related)} items")
    if ad_related: 
        kwds_only = [x['keyword'] for x in ad_related]
        print(f"  First 5: {kwds_only[:5]}")
    
    candidates = set(scraped)
    if ad_related:
        for item in ad_related:
            candidates.add(item['keyword'])
            
    print(f"Total Unique Candidates: {len(candidates)}")
    if not candidates:
        print("FAIL: No candidates found.")
        return

    # 2. Volumes
    candidate_list = list(candidates)[:30]
    vol_map = get_search_volumes_for_keywords(candidate_list)
    print(f"Volume Map: Found data for {len(vol_map)} keywords")
    
    # 3. Filtering and Scoring
    results = []
    for kwd in candidate_list:
        vol_info = vol_map.get(kwd.replace(" ", ""), {})
        total_vol = vol_info.get('total', 0)
        
        if total_vol < 50:
            # print(f"  Skipped {kwd} (Vol: {total_vol})")
            continue
            
        info = get_keyword_info(kwd)
        doc_count = info.get('total', 0)
        score = total_vol / (doc_count + 1) if total_vol > 0 else 0
        
        print(f"  MATCH: {kwd} | Vol: {total_vol} | Docs: {doc_count} | Score: {score:.2f}")
        results.append(kwd)

    print(f"--- Discovery Result: {len(results)} items ---")

if __name__ == "__main__":
    debug_gold("인기아이템")
    debug_gold("가습기")
