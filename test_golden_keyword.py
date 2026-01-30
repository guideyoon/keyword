from naver_service import find_golden_keywords
from dotenv import load_dotenv
import os

def test_golden_keywords():
    load_dotenv()
    
    # 테스트 시드 키워드
    seeds = ["캠핑", "가습기"]
    
    for seed in seeds:
        print(f"\n{'='*50}")
        print(f"발굴 테스트 시작: {seed}")
        print(f"{'='*50}")
        
        # 최소 검색량 500회 이상, 상위 10개 키워드 분석
        results = find_golden_keywords(seed, min_search_vol=500, top_n=10)
        
        if not results:
            print("발굴된 황금 키워드가 없습니다.")
            continue
            
        print(f"\n[결과: '{seed}' 관련 황금 키워드 (경쟁률 낮은 순)]")
        print(f"{'키워드':<20} | {'검색량':<8} | {'문서수':<10} | {'경쟁률'}")
        print("-" * 60)
        
        for res in results:
            print(f"{res['keyword']:<20} | {res['total_vol']:<8} | {res['doc_count']:<10} | {res['competition_rate']}")
            
if __name__ == "__main__":
    test_golden_keywords()
