import os
import requests
import json
from dotenv import load_dotenv, find_dotenv
from bs4 import BeautifulSoup
import time
import hmac
import hashlib
import base64
import re
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

load_dotenv()

def get_realtime_keywords():
    """
    Nate 실시간 이슈 키워드를 가져옵니다.
    """
    try:
        url = "https://www.nate.com/js/data/jsonLiveKeywordDataV1.js?v=1"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        res = requests.get(url, headers=headers)
        res.encoding = 'euc-kr'
        
        data = json.loads(res.text)
        results = []
        for item in data:
            results.append({
                "rank": item[0],
                "keyword": item[1],
                "change": item[2] # 순위 변동 (s:동일, +:상승, -:하락, n:NEW)
            })
            
        return results
    except Exception as e:
        print(f"Realtime keywords error: {e}")
        return []

def get_related_keywords(keyword):
    """
    네이버 통합검색(PC/모바일) 및 자동완성 API를 종합하여 관련 키워드를 추출합니다.
    """
    keywords = set()
    
    # 1. 네이버 자동완성 API (기본 성능 보장)
    try:
        ac_url = "https://ac.search.naver.com/nx/ac"
        ac_params = {
            "q": keyword, "con": "0", "frm": "nv", "ans": "2",
            "r_format": "json", "r_enc": "UTF-8", "rev": "4",
            "q_enc": "UTF-8", "st": "100"
        }
        res_ac = requests.get(ac_url, params=ac_params, timeout=5)
        if res_ac.status_code == 200:
            ac_data = res_ac.json()
            for group in ac_data.get('items', []):
                for item in group:
                    keywords.add(item[0])
    except Exception as e:
        print(f"Autocomplete Error: {e}")

    # 2. 통합검색 페이지 분석 (연관검색어 + 스마트블록 제목)
    search_urls = [
        # PC
        (f"https://search.naver.com/search.naver?query={keyword}", 
         {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}),
        # Mobile (스마트블록 노출이 더 많음)
        (f"https://m.search.naver.com/search.naver?query={keyword}",
         {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36'})
    ]

    stop_words = ["뉴스", "이미지", "인기글", "더보기", "전체", "카페", "블로그", "지식iN", "인플루언서", "동영상", "쇼핑", "지도", "기타"]

    for url, headers in search_urls:
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code != 200: continue
            
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 전통적 연관검색어 selector
            tags = soup.select('.lst_related_srch .tit, .related_srch .tit, .keyword_box .tit, .related_srch .name')
            for tag in tags:
                keywords.add(tag.get_text(strip=True))

            # 스마트블록 제목 (subjectTitle) - HTML 내 JSON 데이터 파싱
            json_matches = re.findall(r'"subjectTitle"\s*:\s*"([^"]+)"', res.text)
            for m in json_matches:
                # 불필요한 노이즈 제거
                if m and m not in stop_words and len(m) < 40:
                    keywords.add(m)

            # 모바일 스마트블록 타이틀 selector
            sb_titles = soup.select('.api_title_area .tit_main, .fds-comps-header-title')
            for sb in sb_titles:
                txt = sb.get_text(strip=True)
                if txt and txt not in stop_words and len(txt) < 40:
                    keywords.add(txt)

        except Exception as e:
            print(f"Search Page Error ({url[:30]}...): {e}")

    # 최종 결과 정제
    final_list = []
    for k in keywords:
        # 검색어 자신 제외 및 불용어 필터링
        if k == keyword: continue
        if any(sw == k for sw in stop_words): continue
        if len(k) < 2: continue # 너무 짧은 키워드 제외
        final_list.append(k)
        
    # 중복 제거 및 가나다 순 정렬
    final_list = sorted(list(set(final_list)))
    
    return final_list

def get_keyword_info(keyword):
    """
    단일 키워드에 대한 기본 정보(문서수 등)를 가져옵니다. (재시도 로직 포함)
    """
    max_retries = 2
    for i in range(max_retries + 1):
        result = search_blog(keyword, display=1)
        if result and 'error' not in result:
            return {'total': result.get('total', 0)}
        
        err_msg = result.get('error', 'Unknown') if result else 'Empty'
        print(f"DEBUG: get_keyword_info retry {i+1} for '{keyword}': {err_msg}")
        if i < max_retries:
            time.sleep(0.5) # Wait before retry
            
    return {'total': 0, 'error': f"Failed after {max_retries} retries"}


def generate_signature(timestamp, method, uri, secret_key):
    message = f"{timestamp}.{method}.{uri}"
    signature = hmac.new(bytes(secret_key, "utf-8"), bytes(message, "utf-8"), hashlib.sha256).digest()
    return base64.b64encode(signature).decode("utf-8")

def get_search_volume(keyword):
    """
    네이버 검색광고 API (RelKwdStat)를 통해 검색어의 PC/모바일 조회수를 조회합니다.
    """
    try:
        # Load keys
        license_key = os.getenv("NAVER_AD_ACCESS_LICENSE")
        secret_key = os.getenv("NAVER_AD_SECRET_KEY")
        customer_id = os.getenv("NAVER_AD_CUSTOMER_ID")
        
        if not license_key or not secret_key or not customer_id:
            return None
            
        base_url = "https://api.naver.com"
        uri = "/keywordstool"
        method = "GET"
        timestamp = str(int(time.time() * 1000))
        
        signature = generate_signature(timestamp, method, uri, secret_key)
        
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "X-Timestamp": timestamp,
            "X-API-KEY": license_key,
            "X-Customer": customer_id, 
            "X-Signature": signature
        }
        
        # hintKeywords allows comma separated list, but we search one by one or batch if needed.
        # Here we just search for the specific keyword.
        # Spaces in hintKeywords cause 400 error, so remove them
        params = {
            "hintKeywords": keyword.replace(" ", ""),
            "showDetail": "1"
        }
        
        res = requests.get(base_url + uri, params=params, headers=headers)
        if res.status_code == 200:
            data = res.json()
            keyword_list = data.get('keywordList', [])
            
            # Find exact match
            for item in keyword_list:
                if item['relKeyword'].replace(" ", "") == keyword.replace(" ", ""):
                    pc_vol = item.get('monthlyPcQcCnt', 0)
                    mo_vol = item.get('monthlyMobileQcCnt', 0)
                    
                    # API returns '< 10' as string for low volume
                    if isinstance(pc_vol, str): pc_vol = 0
                    if isinstance(mo_vol, str): mo_vol = 0
                    
                    comp_idx = item.get('compIdx', 'N/A')
                    
                    return {
                        'pc': pc_vol,
                        'mobile': mo_vol,
                        'total': pc_vol + mo_vol,
                        'comp_idx': comp_idx
                    }
                    
            # If no exact match found in list (should be there if hinted)
            if keyword_list:
                # Fallback to first item? No, risky. 
                pass
                
            return {'pc': 0, 'mobile': 0, 'total': 0}
            
        else:
            print(f"Ad API Error: {res.status_code} {res.text}")
            return None
            
    except Exception as e:
        print(f"Search volume error: {e}")
        return None

        return None

def get_search_volumes_for_keywords(keyword_list):
    """
    주어진 키워드 리스트에 대한 검색량을 조회합니다.
    5개씩 끊어서 Ad API를 호출하여 정확한 데이터를 얻습니다.
    Returns: dict { 'keyword_nospace': {'original_keyword': str, 'pc': int, 'mobile': int, 'total': int} }
    """
    try:
        # Load keys
        license_key = os.getenv("NAVER_AD_ACCESS_LICENSE")
        secret_key = os.getenv("NAVER_AD_SECRET_KEY")
        customer_id = os.getenv("NAVER_AD_CUSTOMER_ID")
        
        if not license_key or not secret_key or not customer_id:
            return {}
            
        base_url = "https://api.naver.com"
        uri = "/keywordstool"
        method = "GET"
        
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "X-API-KEY": license_key,
            "X-Customer": customer_id
        }
        
        final_result = {}
        
        # 5개씩 배칭
        chunk_size = 5
        for i in range(0, len(keyword_list), chunk_size):
            chunk = keyword_list[i:i + chunk_size]
            
            # Clean keywords: remove special characters that might cause 400 error
            clean_chunk = []
            for k in chunk:
                # Remove non-alphanumeric except for space
                cleaned = re.sub(r'[^a-zA-Z0-9가-힣\s]', '', k)
                if cleaned.strip():
                    clean_chunk.append(cleaned.replace(" ", ""))
            
            if not clean_chunk:
                continue
                
            hint_str = ",".join(clean_chunk)
            
            timestamp = str(int(time.time() * 1000))
            signature = generate_signature(timestamp, method, uri, secret_key)
            headers.update({
                "X-Timestamp": timestamp,
                "X-Signature": signature
            })
            
            params = {
                "hintKeywords": hint_str,
                "showDetail": "1"
            }
            
            # API 호출
            res = requests.get(base_url + uri, params=params, headers=headers)
            
            if res.status_code == 200:
                data = res.json()
                for item in data.get('keywordList', []):
                    kwd = item['relKeyword']
                    # API 결과가 입력한 키워드(공백제거)와 일치하는 것만 저장 (또는 전체 저장하여 hit rate 높임)
                    # 여기서는 우리가 요청한 chunk에 있는 것들을 우선적으로 찾아서 매핑해야 함.
                    # 하지만 API는 관련 키워드를 더 많이 줌.
                    # 효율성을 위해 일단 다 저장하되, key는 공백제거로 통일
                    
                    pc_vol = item.get('monthlyPcQcCnt', 0)
                    mo_vol = item.get('monthlyMobileQcCnt', 0)
                    if isinstance(pc_vol, str): pc_vol = 0
                    if isinstance(mo_vol, str): mo_vol = 0
                    
                    comp_idx = item.get('compIdx', 'N/A')
                    
                    final_result[kwd.replace(" ", "")] = {
                        'original_keyword': kwd,
                        'pc': pc_vol,
                        'mobile': mo_vol,
                        'total': pc_vol + mo_vol,
                        'comp_idx': comp_idx
                    }
                # Rate limit safety (optional, but 5 keywords per call is rare)
                time.sleep(0.1)
            else:
                print(f"Batch Ad API Error: {res.status_code} {res.text}")
                
        return final_result
            
    except Exception as e:
        print(f"Bulk search volume error: {e}")
        return {}

def get_related_keywords_from_ad_api(seed_keyword):
    """
    네이버 검색광고 API를 사용하여 연관 키워드 대량(최대 1000개)과 그 검색량을 가져옵니다.
    """
    try:
        license_key = os.getenv("NAVER_AD_ACCESS_LICENSE")
        secret_key = os.getenv("NAVER_AD_SECRET_KEY")
        customer_id = os.getenv("NAVER_AD_CUSTOMER_ID")
        
        if not license_key or not secret_key or not customer_id:
            return []
            
        base_url = "https://api.naver.com"
        uri = "/keywordstool"
        method = "GET"
        timestamp = str(int(time.time() * 1000))
        signature = generate_signature(timestamp, method, uri, secret_key)
        
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "X-Timestamp": timestamp,
            "X-API-KEY": license_key,
            "X-Customer": customer_id, 
            "X-Signature": signature
        }
        
        params = {
            "hintKeywords": re.sub(r'[^a-zA-Z0-9가-힣\s]', '', seed_keyword).replace(" ", ""),
            "showDetail": "1"
        }
        
        res = requests.get(base_url + uri, params=params, headers=headers)
        if res.status_code == 200:
            data = res.json()
            keyword_list = data.get('keywordList', [])
            
            results = []
            for item in keyword_list:
                pc_vol = item.get('monthlyPcQcCnt', 0)
                mo_vol = item.get('monthlyMobileQcCnt', 0)
                if isinstance(pc_vol, str): pc_vol = 0
                if isinstance(mo_vol, str): mo_vol = 0
                
                comp_idx = item.get('compIdx', 0)
                
                results.append({
                    'keyword': item['relKeyword'],
                    'pc': pc_vol,
                    'mobile': mo_vol,
                    'total': pc_vol + mo_vol,
                    'comp_idx': comp_idx
                })
            return results
        else:
            print(f"Ad API Error: {res.status_code}")
            return []
    except Exception as e:
        print(f"Discovery error: {e}")
        return []

def get_blog_rank(keyword):
    """
    키워드로 검색했을 때 'VIEW' 영역의 상위 노출 컨텐츠가 블로그인지 카페인지 분석합니다.
    Returns: list of strings ("B" for Blog, "C" for Cafe, etc.)
    """
    try:
        # PC Search URL
        url = f"https://search.naver.com/search.naver?query={keyword}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        ranks = []
        
        # 'view_wrap' usually contains the list of VIEW results
        # Look for items in the VIEW section. New structure often has 'view_wrap'.
        view_section = soup.select_one(".view_wrap") or soup.select_one(".api_subject_bx")
        
        if view_section:
            items = view_section.select("li.bx")
            for item in items:
                text_content = item.get_text()
                # Simple heuristic check based on typical labels
                if "블로그" in text_content:
                    ranks.append("B") 
                elif "카페" in text_content:
                    ranks.append("C") 
                else:
                    # Sometimes simpler structure
                    ranks.append("?")
                
                if len(ranks) >= 10:
                    break
        else:
            # Fallback for 'Smart Block' or different layouts
            # Just grab generic 'bx' items that look like content
            items = soup.select("li.bx")
            for item in items:
                txt = item.get_text()
                if "블로그" in txt: ranks.append("B")
                elif "카페" in txt: ranks.append("C")
                if len(ranks) >= 10: break

        return ranks
    except Exception as e:
        print(f"Blog rank error: {e}")
        return []


def get_api_keys():
    client_id = os.getenv("NAVER_CLIENT_ID", "").strip()
    client_secret = os.getenv("NAVER_CLIENT_SECRET", "").strip()
    return client_id, client_secret

def search_blog(keyword, display=10, sort='sim'):
    """
    네이버 블로그 검색 API를 호출합니다.
    :param keyword: 검색어
    :param display: 표시할 결과 수 (1~100)
    :param sort: 정렬 순서 (sim: 정확도순, date: 날짜순)
    :return: 결과 딕셔너리 (total, items 등) 또는 None (에러 시)
    """
    client_id, client_secret = get_api_keys()
    
    if not client_id or not client_secret:
        return {"error": "API 키가 설정되지 않았습니다. .env 파일을 확인해주세요."}

    encText = requests.utils.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/blog?query={encText}&display={display}&sort={sort}"

    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Error Code: {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": str(e)}

def search_news(keyword, display=10, sort='sim'):
    """
    네이버 뉴스 검색 API를 호출합니다.
    """
    return _search_general('news', keyword, display, sort)

def search_shop(keyword, display=10, sort='sim'):
    """
    네이버 쇼핑 검색 API를 호출합니다.
    """
    return _search_general('shop', keyword, display, sort)

def search_kin(keyword, display=10, sort='sim'):
    """
    네이버 지식iN 검색 API를 호출합니다.
    """
    return _search_general('kin', keyword, display, sort)

def _search_general(service_type, keyword, display=10, sort='sim'):
    """
    네이버 검색 API 공통 호출 함수
    """
    client_id, client_secret = get_api_keys()
    
    if not client_id or not client_secret:
        return {"error": "API 키가 설정되지 않았습니다. .env 파일을 확인해주세요."}

    encText = requests.utils.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/{service_type}?query={encText}&display={display}&sort={sort}"

    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Error Code: {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": str(e)}

def get_naver_section_order(keyword):
    """
    PC와 모바일의 네이버 검색 결과 섹션 순서를 분석합니다.
    """
    results = {'pc': [], 'mobile': []}
    
    # 알려진 섹션 이름 목록
    known_sections = ["뉴스", "블로그", "쇼핑", "지식iN", "이미지", "어학사전", "인플루언서", "지도", "동영상", "웹문서"]
    noise = ["문서 저장하기", "Keep에 저장", "Keep 바로가기", "AD", "도움말", "VIEW", "더보기"]
    
    # 섹션 추출 헬퍼 함수
    def extract_sections(soup, device='pc'):
        sections = []
        seen_titles = set()
        
        # 방법 1: 섹션 컨테이너에서 직접 추출 (section.sc_new, div.api_subject_bx 등)
        section_containers = soup.select('section.sc_new, div.api_subject_bx, section[class*="sc_new"]')
        
        for container in section_containers:
            # 각 컨테이너 내에서 헤더 찾기
            headers = container.select('.api_title, h2, .tit_main, .title_link, h3.title, .area_title')
            
            for h in headers:
                text = h.get_text(strip=True)
                if not text or text in seen_titles or text == keyword:
                    continue
                
                # 노이즈 필터링
                if text in noise or len(text) > 30:
                    continue
                
                # 알려진 섹션이거나 짧은 텍스트면 추가
                if text in known_sections or (len(text) < 20 and text not in noise):
                    sections.append(text)
                    seen_titles.add(text)
        
        # 방법 2: 모든 헤더 후보를 다시 검사 (더 포괄적)
        all_headers = soup.select('.api_title, h2, .tit_main, .title_link, h3.title, .area_title')
        
        for h in all_headers:
            text = h.get_text(strip=True)
            if not text or text in seen_titles:
                continue
            
            if text in noise or len(text) > 30:
                continue
            
            # 부모 태그 확인하여 유효한 섹션인지 검증
            curr = h
            valid = False
            for _ in range(5):
                curr = curr.parent
                if not curr:
                    break
                classes = curr.get('class', [])
                if (curr.name == 'section' and 'sc_new' in ' '.join(classes)) or \
                   (curr.get('class') and 'api_subject_bx' in classes):
                    valid = True
                    break
            
            if valid:
                if text in known_sections or (len(text) < 20 and text not in noise):
                    if text not in seen_titles:
                        sections.append(text)
                        seen_titles.add(text)
        
        # 방법 3: 알려진 섹션 이름이 HTML에 있으면 직접 검색 (뉴스 등 빠진 경우 대비)
        for known_sec in known_sections:
            if known_sec not in seen_titles:
                # HTML에서 해당 텍스트를 포함하는 요소 찾기
                elements = soup.find_all(string=lambda s: s and known_sec in s.strip())
                for el in elements[:10]:  # 최대 10개만 확인
                    parent = el.parent
                    # 섹션 컨테이너 내부인지 확인
                    for _ in range(5):
                        if not parent:
                            break
                        classes = parent.get('class', [])
                        if (parent.name == 'section' and 'sc_new' in ' '.join(classes)) or \
                           'api_subject_bx' in classes:
                            sections.append(known_sec)
                            seen_titles.add(known_sec)
                            break
                        parent = parent.parent
                    if known_sec in seen_titles:
                        break
        
        return sections
    
    # 1. PC 검색 결과 분석
    try:
        url_pc = f"https://search.naver.com/search.naver?query={keyword}"
        headers_pc = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        res_pc = requests.get(url_pc, headers=headers_pc)
        soup_pc = BeautifulSoup(res_pc.text, 'html.parser')
        
        sections_pc = extract_sections(soup_pc, 'pc')
        results['pc'] = sections_pc
        
    except Exception as e:
        print(f"PC parsing error: {e}")
        results['pc'] = ["오류 발생"]

    # 2. 모바일 검색 결과 분석
    try:
        url_mo = f"https://m.search.naver.com/search.naver?query={keyword}"
        headers_mo = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36'
        }
        res_mo = requests.get(url_mo, headers=headers_mo)
        soup_mo = BeautifulSoup(res_mo.text, 'html.parser')
        
        sections_mo = extract_sections(soup_mo, 'mobile')
        results['mobile'] = sections_mo

    except Exception as e:
        print(f"Mobile parsing error: {e}")
        results['mobile'] = ["오류 발생"]
        
    return results

def get_google_trending_keywords(country_code='KR', limit=20):
    """
    구글 트렌드의 실시간 급상승 키워드를 가져옵니다.
    pytrends 라이브러리를 우선 사용하고, 실패시 다른 방법 시도합니다.
    
    Args:
        country_code: 국가 코드 (KR: 한국, US: 미국 등)
        limit: 가져올 키워드 개수
    
    Returns:
        List of dict: [{"rank": 1, "keyword": "키워드", "traffic": "N/A"}, ...]
    """
    results = []
    
    # 방법 1: pytrends 라이브러리 사용 (가장 안정적)
    try:
        from pytrends.request import TrendReq
        
        # pytrends 초기화
        pytrends = TrendReq(hl='ko', tz=540, timeout=(10, 25))
        
        # trending_searches 함수 사용 (pandas DataFrame 반환)
        try:
            trending_df = pytrends.trending_searches(pn=country_code)
            
            if trending_df is not None and len(trending_df) > 0:
                # DataFrame의 첫 번째 컬럼에서 키워드 추출
                if hasattr(trending_df, 'iloc'):
                    rank = 1
                    for idx in range(min(limit, len(trending_df))):
                        keyword = str(trending_df.iloc[idx, 0]).strip()
                        if keyword and keyword != 'nan':
                            results.append({
                                "rank": rank,
                                "keyword": keyword,
                                "traffic": "N/A"
                            })
                            rank += 1
                else:
                    # 리스트 형태인 경우
                    keywords_list = list(trending_df[0]) if isinstance(trending_df, list) else trending_df.tolist()
                    rank = 1
                    for keyword in keywords_list[:limit]:
                        keyword_str = str(keyword).strip()
                        if keyword_str and keyword_str != 'nan':
                            results.append({
                                "rank": rank,
                                "keyword": keyword_str,
                                "traffic": "N/A"
                            })
                            rank += 1
                        
        except Exception as e:
            print(f"pytrends trending_searches error: {e}")
            import traceback
            traceback.print_exc()
            
    except ImportError:
        print("pytrends 라이브러리가 설치되지 않았습니다. 'pip install pytrends'를 실행해주세요.")
    except Exception as e:
        print(f"pytrends initialization error: {e}")
    
    # 방법 2: pytrends가 실패한 경우 Google Trends JSON API 시도
    if not results:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": "https://trends.google.com/",
            }
            
            # Google Trends의 내부 JSON API 엔드포인트
            url = f"https://trends.google.com/trends/api/dailytrends?hl=ko&geo={country_code}&ns=15"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200 and response.text:
                # Google Trends API는 ")]}',"로 시작하는 경우가 있음
                content = response.text
                if content.startswith(")]}',"):
                    content = content[5:]  # 제거
                
                try:
                    data = json.loads(content)
                    
                    # JSON 구조 파싱
                    if 'default' in data and 'trendingSearchesDays' in data['default']:
                        for day_data in data['default']['trendingSearchesDays']:
                            if 'trendingSearches' in day_data:
                                rank = 1
                                for trend in day_data['trendingSearches']:
                                    if rank > limit:
                                        break
                                    
                                    if 'title' in trend and 'query' in trend['title']:
                                        keyword = trend['title']['query']
                                        
                                        # 트래픽 정보
                                        traffic = "N/A"
                                        if 'formattedTraffic' in trend:
                                            traffic = trend['formattedTraffic']
                                        
                                        if keyword not in [r['keyword'] for r in results]:
                                            results.append({
                                                "rank": rank,
                                                "keyword": keyword,
                                                "traffic": traffic
                                            })
                                            rank += 1
                                
                                if results:
                                    break  # 첫 번째 날 데이터만 사용
                                    
                except json.JSONDecodeError as e:
                    print(f"JSON Parse Error: {e}")
                    
        except Exception as e:
            print(f"Google Trends JSON API Error: {e}")
    
    # 방법 3: RSS/Atom 피드 백업 (마지막 방법)
    if not results:
        try:
            # 국가 코드 매핑 (RSS 피드용)
            country_map = {
                'KR': 'p23',
                'US': 'p1',
                'JP': 'p27',
                'CN': 'p36',
                'GB': 'p9'
            }
            pn = country_map.get(country_code, 'p23')
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/atom+xml,application/xml,text/xml,*/*",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": "https://trends.google.com/",
            }
            
            # 여러 URL 패턴 시도
            urls_to_try = [
                f"https://trends.google.com/trends/hottrends/atom/feed?pn={pn}",
                f"https://trends.google.co.kr/trends/hottrends/atom/feed?pn={pn}",
                f"https://trends.google.com/trends/trendingsearches/daily/rss?geo={country_code}",
            ]
            
            for url in urls_to_try:
                if len(results) >= limit:
                    break
                    
                try:
                    response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
                    
                    if response.status_code == 200 and response.content:
                        # XML/Atom 파싱 시도
                        try:
                            # 에러가 발생할 수 있는 문자 제거
                            content = response.content.decode('utf-8', errors='ignore')
                            
                            # XML 파싱
                            root = ET.fromstring(content)
                            
                            # Atom 피드 형식 파싱
                            rank = 1
                            items = root.findall('.//item') or root.findall('.//entry')
                            
                            for item in items:
                                if rank > limit:
                                    break
                                
                                keyword = None
                                
                                # title 태그 찾기 (다양한 네임스페이스 지원)
                                title_elem = item.find('.//title')
                                if title_elem is None:
                                    # 네임스페이스가 있는 경우
                                    for ns in ['', '{http://www.w3.org/2005/Atom}']:
                                        title_elem = item.find(f'{ns}title')
                                        if title_elem is not None:
                                            break
                                
                                if title_elem is not None and title_elem.text:
                                    keyword = title_elem.text.strip()
                                    
                                    # HTML 태그 제거
                                    if '<' in keyword:
                                        keyword = re.sub(r'<[^>]+>', '', keyword).strip()
                                
                                if keyword and keyword not in [r['keyword'] for r in results]:
                                    # 트래픽 정보 시도
                                    traffic = "N/A"
                                    for elem in item.iter():
                                        tag_text = elem.tag if isinstance(elem.tag, str) else str(elem.tag)
                                        if 'traffic' in tag_text.lower() or 'approx' in tag_text.lower():
                                            if elem.text:
                                                traffic = elem.text.strip()
                                            break
                                    
                                    results.append({
                                        "rank": rank,
                                        "keyword": keyword,
                                        "traffic": traffic
                                    })
                                    rank += 1
                            
                            if results:
                                break  # 성공했으면 다음 URL 시도 안 함
                                
                        except ET.ParseError as e:
                            print(f"XML Parse Error for {url}: {e}")
                            continue
                        except Exception as e:
                            print(f"Parse Error for {url}: {e}")
                            continue
                            
                except requests.exceptions.RequestException as e:
                    print(f"Request Error for {url}: {e}")
                    continue
                except Exception as e:
                    print(f"Unexpected Error for {url}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Google Trends RSS Error: {e}")
    
    return results

def get_datalab_shopping_trends(cid):
    """
    네이버 데이터랩 쇼핑 인사이트에서 분야별 인기 검색어를 가져옵니다.
    Ref: https://datalab.naver.com/shoppingInsight/sCategory.naver
    """
    url = "https://datalab.naver.com/shoppingInsight/getCategoryKeywordRank.naver"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Referer": "https://datalab.naver.com/shoppingInsight/sCategory.naver",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://datalab.naver.com"
    }

    # 최근 2일 전 데이터를 조회 (데이터랩 업데이트 주기에 맞춤)
    today = datetime.now()
    end_date = (today - timedelta(days=2)).strftime("%Y-%m-%d")
    start_date = (today - timedelta(days=3)).strftime("%Y-%m-%d")
    
    data = {
        "cid": str(cid),
        "timeUnit": "date",
        "startDate": start_date,
        "endDate": end_date,
        "age": "",
        "gender": "",
        "device": "",
        "page": 1,
        "count": 20
    }
    
    try:
        res = requests.post(url, headers=headers, data=data)
        if res.status_code == 200:
            result = res.json()
            # ranks: [{rank, keyword, linkId}, ...]
            return result.get('ranks', [])
        else:
            print(f"DataLab API Failed: {res.status_code}")
            return []
    except Exception as e:
        print(f"DataLab API Error: {e}")
        return []

def get_related_ad_keywords(keyword):
    """
    네이버 검색 광고 API를 통해 관련 키워드 리스트를 가져옵니다.
    """
    try:
        license_key = os.getenv("NAVER_AD_ACCESS_LICENSE")
        secret_key = os.getenv("NAVER_AD_SECRET_KEY")
        customer_id = os.getenv("NAVER_AD_CUSTOMER_ID")
        
        if not license_key or not secret_key or not customer_id:
            print("Ad API keys missing")
            return []
            
        base_url = "https://api.naver.com"
        uri = "/keywordstool"
        method = "GET"
        timestamp = str(int(time.time() * 1000))
        signature = generate_signature(timestamp, method, uri, secret_key)
        
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "X-Timestamp": timestamp,
            "X-API-KEY": license_key,
            "X-Customer": customer_id, 
            "X-Signature": signature
        }
        
        params = {
            "hintKeywords": keyword.replace(" ", ""),
            "showDetail": "1"
        }
        
        res = requests.get(base_url + uri, params=params, headers=headers)
        if res.status_code == 200:
            data = res.json()
            return data.get('keywordList', [])
        else:
            print(f"Ad API Error: {res.status_code} {res.text}")
            return []
    except Exception as e:
        print(f"Error fetching AD keywords: {e}")
        return []

def find_golden_keywords(seed_keyword, min_search_vol=500, top_n=30):
    """
    황금 키워드를 발굴합니다.
    1. 검색광고 API로 관련 키워드 및 검색량 수집
    2. 필터링 및 상위 키워드 선정
    3. 블로그 검색 API로 문서수 수집
    4. 황금지수 계산 및 정렬
    """
    print(f"Starting Golden Keyword discovery for: {seed_keyword}")
    
    # 1. 릴레이션 키워드 수집
    ad_keywords = get_related_ad_keywords(seed_keyword)
    if not ad_keywords:
        return []
    
    # 2. 1차 필터링 및 정렬 (검색량 기준)
    candidates = []
    for item in ad_keywords:
        kw = item['relKeyword']
        pc_vol = item.get('monthlyPcQcCnt', 0)
        mo_vol = item.get('monthlyMobileQcCnt', 0)
        
        # API가 '< 10'을 문자열로 주기도 함
        if isinstance(pc_vol, str): pc_vol = 5
        if isinstance(mo_vol, str): mo_vol = 5
        
        total_vol = pc_vol + mo_vol
        
        if total_vol >= min_search_vol:
            candidates.append({
                'keyword': kw,
                'pc_vol': pc_vol,
                'mo_vol': mo_vol,
                'total_vol': total_vol
            })
            
    # 검색량 높은 순으로 정렬하여 상위 N개 선정
    candidates = sorted(candidates, key=lambda x: x['total_vol'], reverse=True)[:top_n]
    
    # 3. 문서 수 수집 및 황금지수 계산
    results = []
    for item in candidates:
        kw = item['keyword']
        # 블로그 검색 API로 문서수(total) 가져오기
        blog_info = get_keyword_info(kw)
        doc_count = blog_info.get('total', 0)
        
        # 황금률(경쟁 강도) = (문서 수 / 월간 검색량)
        # 낮을수록 좋음 (검색량 대비 문서가 적음)
        competition_rate = round((doc_count / item['total_vol']) if item['total_vol'] > 0 else 999, 2)
        
        results.append({
            'keyword': kw,
            'total_vol': item['total_vol'],
            'pc_vol': item['pc_vol'],
            'mo_vol': item['mo_vol'],
            'doc_count': doc_count,
            'competition_rate': competition_rate
        })
        # API 속도 제한 고려
        time.sleep(0.1)
        
    # 경쟁률 낮은 순(황금 키워드)으로 정렬
    results = sorted(results, key=lambda x: x['competition_rate'])
    
    return results


def analyze_top_blogs(keyword, count=5):
    """
    키워드의 상위 블로그를 분석하여 경쟁 난이도 정보를 반환합니다.
    
    Returns:
        dict: {
            'keyword': str,
            'top_posts': list of post info,
            'avg_length': int (평균 글자수 추정),
            'difficulty': str (쉬움/보통/어려움),
            'difficulty_score': int (0-100),
            'recommendation': str
        }
    """
    try:
        # 1. 네이버 블로그 검색 API로 상위 포스트 가져오기
        blog_result = search_blog(keyword, display=count, sort='sim')
        
        if 'error' in blog_result:
            return {'error': blog_result['error'], 'keyword': keyword}
        
        items = blog_result.get('items', [])
        if not items:
            return {
                'keyword': keyword,
                'top_posts': [],
                'avg_length': 0,
                'difficulty': '알수없음',
                'difficulty_score': 0,
                'recommendation': '데이터 없음'
            }
        
        # 2. 각 포스트 분석
        top_posts = []
        total_desc_len = 0
        fresh_count = 0  # 최근 30일 내 포스트 수
        
        for item in items:
            title = BeautifulSoup(item.get('title', ''), 'html.parser').get_text()
            description = BeautifulSoup(item.get('description', ''), 'html.parser').get_text()
            blogger_name = item.get('bloggername', '')
            post_date_str = item.get('postdate', '')
            link = item.get('link', '')
            
            # 날짜 파싱 (YYYYMMDD 형식)
            days_ago = 999
            if post_date_str and len(post_date_str) == 8:
                try:
                    post_date = datetime.strptime(post_date_str, '%Y%m%d')
                    days_ago = (datetime.now() - post_date).days
                    if days_ago <= 30:
                        fresh_count += 1
                except:
                    pass
            
            # 설명 길이 (실제 글자수의 대략적 지표)
            desc_len = len(description)
            total_desc_len += desc_len
            
            top_posts.append({
                'title': title,
                'blogger': blogger_name,
                'desc_length': desc_len,
                'days_ago': days_ago,
                'link': link
            })
        
        # 3. 난이도 계산
        avg_desc_len = total_desc_len // len(items) if items else 0
        freshness_ratio = fresh_count / len(items) if items else 0
        
        # 난이도 점수 (0-100)
        # 설명 길이가 길수록, 최신 글이 많을수록 경쟁이 치열함
        length_score = min(avg_desc_len / 3, 50)  # 최대 50점
        freshness_score = freshness_ratio * 50   # 최대 50점
        difficulty_score = int(length_score + freshness_score)
        
        # 등급 판정
        if difficulty_score < 30:
            difficulty = '🟢 쉬움'
            recommendation = '지금 바로 글을 작성하세요! 경쟁이 낮습니다.'
        elif difficulty_score < 60:
            difficulty = '🟡 보통'
            recommendation = '양질의 콘텐츠로 충분히 상위노출 가능합니다.'
        else:
            difficulty = '🔴 어려움'
            recommendation = '장문의 고퀄리티 콘텐츠가 필요합니다. 인플루언서 경쟁 주의.'
        
        return {
            'keyword': keyword,
            'top_posts': top_posts,
            'avg_length': avg_desc_len * 10,  # 설명 → 예상 본문 길이로 환산
            'difficulty': difficulty,
            'difficulty_score': difficulty_score,
            'freshness_ratio': round(freshness_ratio * 100),
            'recommendation': recommendation
        }
        
    except Exception as e:
        print(f"analyze_top_blogs error: {e}")
        return {'error': str(e), 'keyword': keyword}
