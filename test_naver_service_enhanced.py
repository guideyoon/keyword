from naver_service import get_related_keywords

def test_extraction():
    test_keywords = ["하윤경", "제습기 추천", "아이폰 15"]
    
    for kw in test_keywords:
        print(f"\n[Testing Keyword: {kw}]")
        results = get_related_keywords(kw)
        if results:
            print(f"Found {len(results)} related keywords:")
            for i, r in enumerate(results[:15], 1): # Show up to 15
                print(f"  {i}. {r}")
            if len(results) > 15:
                print(f"  ... and {len(results)-15} more")
        else:
            print("No keywords found.")
        print("-" * 40)

if __name__ == "__main__":
    test_extraction()
