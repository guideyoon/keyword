from naver_service import get_naver_section_order

def test_section_order(keyword):
    print(f"Testing keyword: {keyword}")
    result = get_naver_section_order(keyword)
    print("PC Sections:", result['pc'])
    print("Mobile Sections:", result['mobile'])
    
    if not result['pc']:
        print("WARNING: PC sections empty")
    if not result['mobile']:
        print("WARNING: Mobile sections empty")

if __name__ == "__main__":
    test_section_order("강남 맛집")
    test_section_order("정보처리기사")
