from naver_service import get_naver_section_order
import time

def test_section_order():
    kwd = "로봇청소기"
    print(f"Testing section order for '{kwd}'...")
    start = time.time()
    sections = get_naver_section_order(kwd)
    end = time.time()
    print(f"Time taken: {end - start:.2f}s")
    print(f"Sections (PC): {sections.get('pc', [])}")
    print(f"Sections (Mobile): {sections.get('mobile', [])}")

if __name__ == "__main__":
    test_section_order()
