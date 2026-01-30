
from naver_service import search_news, search_kin
import json

def check():
    print("NEWS ITEM KEYS:")
    news = search_news("테스트", display=1)
    if news and 'items' in news and news['items']:
        print(news['items'][0].keys())
        print("Sample pubDate:", news['items'][0].get('pubDate'))
    
    print("\nKIN ITEM KEYS:")
    kin = search_kin("테스트", display=1)
    if kin and 'items' in kin and kin['items']:
        print(kin['items'][0].keys())
        # Check potential date fields
        print("Sample item:", json.dumps(kin['items'][0], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    check()
