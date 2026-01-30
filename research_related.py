import requests
from bs4 import BeautifulSoup

def find_related_keywords(keyword):
    url = f"https://search.naver.com/search.naver?query={keyword}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print(f"Fetching {url}")
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # Try common selectors for related keywords
    # 1. 'related_srch' section
    keywords = []
    
    with open("debug_naver.html", "w", encoding="utf-8") as f:
        f.write(soup.prettify())
        print("Dumped HTML to debug_naver.html")
    
    # Debug: Print all text to see if we even got the page content
    # print(soup.get_text()[:500])
    
    # Try finding div with class 'related_srch'
    divs = soup.select('div.related_srch')
    if divs:
        print(f"Found {len(divs)} divs with class 'related_srch'")
        for d in divs:
            print(d.get_text(strip=True))
            
            
    # Try filtering by text '연관 검색어' or '관련키워드'
    import re
    target = soup.find(string=re.compile("연관 검색어|관련키워드"))
    if target:
        print(f"Found '{target}' text in: {target.parent.name}")
        # walk up and find the container
        curr = target.parent
        for _ in range(5):
             if curr.name == 'div' or curr.name == 'section':
                 print(f"Container candidate: <{curr.name} class={curr.get('class')}>")
                 # Check children text
                 # print(curr.get_text(separator='|', strip=True))
                 
                 # Try to find list items here
                 if curr.select('.tit'):
                     for t in curr.select('.tit'):
                         print(f"  - {t.get_text()}")
                         keywords.append(t.get_text())
                 elif curr.select('a'):
                     # Sometimes they are just links
                     for a in curr.select('a'):
                         if a.get_text(strip=True) and len(a.get_text(strip=True)) < 20: 
                            print(f"  - (link) {a.get_text()}")
                 break
             curr = curr.parent

            
    # Method 2: generic class names often used by Naver
    if not keywords:
        for tag in soup.select('.lst_related_srch .tit'):
             keywords.append(tag.get_text(strip=True))
             
    print(f"Found Keywords: {keywords}")

if __name__ == "__main__":
    find_related_keywords("제습기 추천")
