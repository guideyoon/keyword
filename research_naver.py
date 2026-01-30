import requests
from bs4 import BeautifulSoup
import re

def analyze_naver_search(keyword, device='pc'):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    if device == 'mobile':
        url = f"https://m.search.naver.com/search.naver?query={keyword}"
        headers['User-Agent'] = 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36'
    else:
        url = f"https://search.naver.com/search.naver?query={keyword}"

    print(f"Fetching {url}...")
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    sections = []
    
    print(f"[{device.upper()}] status: {response.status_code}")
    
    # Debug: Search for known section titles in the raw text to see where they are
    targets = ["VIEW", "뉴스", "쇼핑", "지식iN", "이미지", "어학사전", "인플루언서"]
    
    for t in targets:
        if t in response.text:
            print(f"Found '{t}' in response text.")
            # Let's try to find the container
            # Using soup to find text and parent keys
            elements = soup.find_all(string=re.compile(t))
            for el in elements[:3]: # check first 3 matches
                parent = el.parent
                # print(f"  Parent of '{t}': {parent.name} class={parent.get('class')}")
                # Traverse up to find a section or div with id/class
                curr = parent
                found_section = False
                for _ in range(5):
                    if curr.name == 'section' or (curr.get('class') and 'api_subject_bx' in curr.get('class', [])):
                         print(f"  '{t}' belongs to: <{curr.name} class='{curr.get('class')}'>")
                         found_section = True
                         break
                    curr = curr.parent
                    if not curr: break
                if not found_section:
                    pass # print(f"  '{t}' container not found in 5 moves up")

    # Re-try extraction with broadened selectors
    sections = []
    # Common classes for headers
    header_candidates = soup.select('.api_title, .tit_main, .title_link, h2')
    
    seen_titles = set()
    for h in header_candidates:
        text = h.get_text(strip=True)
        # Naver sometimes puts 'VIEW' in a link inside h2
        if not text: continue
        
        # Check if this header is likely a section header
        # Usually inside a section.sc_new or div.api_subject_bx
        curr = h
        valid = False
        for _ in range(3):
            curr = curr.parent
            if not curr: break
            if curr.name == 'section' or (curr.get('class') and 'api_subject_bx' in curr.get('class', [])):
                valid = True
                break
        
        if valid and text not in seen_titles:
            sections.append(text)
            seen_titles.add(text)
            
    # Filter out common noise
    noise = ["문서 저장하기", "Keep에 저장", "Keep 바로가기", "AD"]
    sections = [s for s in sections if s not in noise and len(s) < 20]

    print(f"[{device.upper()}] Refined Sections: {sections}")

if __name__ == "__main__":
    analyze_naver_search("강남 맛집", "pc")
    analyze_naver_search("강남 맛집", "mobile")
