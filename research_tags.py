import requests
from bs4 import BeautifulSoup

def find_tags(keyword):
    url = f"https://search.naver.com/search.naver?query={keyword}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36'
    }
    
    print(f"Fetching {url}")
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    # Hints from screenshot: "제습기 추천 1등급", "제습기 추천 lg"
    # Search for "1등급"
    import re
    targets = soup.find_all(string=re.compile("1등급"))
    
    if targets:
        print(f"Found {len(targets)} occurrences of '1등급'")
        for t in targets:
            print(f"Match: '{t}'")
            print("Parent Chain:")
            curr = t.parent
            for i in range(5):
                attrs = curr.attrs if curr else {}
                print(f"  [{i}] <{curr.name} {attrs}>")
                curr = curr.parent
                if not curr: break
            print("-" * 20)
    else:
        print("Text '1등급' NOT found.")
        # Fallback: dump all generic lists
        for ul in soup.select('ul'):
             # check if many items
             lis = ul.select('li')
             if len(lis) > 5:
                  txt = [li.get_text(strip=True) for li in lis]
                  # print(f"List with {len(lis)} items: {txt[:3]}...")

if __name__ == "__main__":
    find_tags("제습기 추천")
