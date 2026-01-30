import requests
from bs4 import BeautifulSoup
import re
import json

def extract_related_keywords(keyword):
    print(f"Searching for: {keyword}")
    
    # 1. PC Search Result Analysis
    url_pc = f"https://search.naver.com/search.naver?query={keyword}"
    headers_pc = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    keywords = set()
    
    try:
        res_pc = requests.get(url_pc, headers=headers_pc)
        soup_pc = BeautifulSoup(res_pc.text, 'html.parser')
        
        # Method A: Traditional Related Search (연관검색어)
        # Often in div.related_srch or similar
        related_tags = soup_pc.select('.lst_related_srch .tit, .related_srch .tit, .tit_related_srch')
        for tag in related_tags:
            keywords.add(tag.get_text(strip=True))
            
        # Method B: Smart Block / Intent Block (JSON extraction)
        # Look for subjectTitle in script tags
        scripts = soup_pc.find_all('script')
        for script in scripts:
            content = script.string
            if content and 'subjectTitle' in content:
                # Extract all occurrences of "subjectTitle":"..."
                matches = re.findall(r'"subjectTitle"\s*:\s*"([^"]+)"', content)
                for m in matches:
                    if m and m != keyword:
                        keywords.add(m)
        
    except Exception as e:
        print(f"PC Search Error: {e}")

    # 2. Mobile Search Result Analysis (Better for Smart Blocks)
    url_mo = f"https://m.search.naver.com/search.naver?query={keyword}"
    headers_mo = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36'
    }
    
    try:
        res_mo = requests.get(url_mo, headers=headers_mo)
        soup_mo = BeautifulSoup(res_mo.text, 'html.parser')
        
        # Method A: Mobile Related Keywords
        # class: .related_srch, .keyword_box
        mo_tags = soup_mo.select('.keyword_box .tit, .related_srch .name, .api_title_area .tit_main')
        for tag in mo_tags:
            txt = tag.get_text(strip=True)
            if txt and len(txt) < 30:
                keywords.add(txt)
                
        # Method B: Smart Block Titles
        # Mobile often has explicit sections for Smart Blocks
        smart_blocks = soup_mo.select('.api_title_area .tit_main, .fds-comps-header-title')
        for sb in smart_blocks:
            txt = sb.get_text(strip=True)
            # Filter noise
            if txt and "광고" not in txt and len(txt) < 30 and txt != "인기 주제":
                keywords.add(txt)
                
    except Exception as e:
        print(f"Mobile Search Error: {e}")

    # 3. Naver Autocomplete (Bonus)
    try:
        ac_url = "https://ac.search.naver.com/nx/ac"
        ac_params = {
            "q": keyword,
            "con": "0",
            "frm": "nv",
            "ans": "2",
            "r_format": "json",
            "r_enc": "UTF-8",
            "rev": "4",
            "q_enc": "UTF-8",
            "st": "100"
        }
        res_ac = requests.get(ac_url, params=ac_params)
        ac_data = res_ac.json()
        for group in ac_data.get('items', []):
            for item in group:
                keywords.add(item[0])
    except Exception as e:
        print(f"Autocomplete Error: {e}")

    # Final cleanup
    result_list = sorted(list(keywords))
    if keyword in result_list:
        result_list.remove(keyword)
        
    return result_list

if __name__ == "__main__":
    # Test with user-specific examples
    test_keywords = ["하윤경", "제습기 추천"]
    for k in test_keywords:
        results = extract_related_keywords(k)
        print(f"\nFinal Keywords for '{k}':")
        for i, word in enumerate(results, 1):
            print(f"{i}. {word}")
        print("-" * 30)
