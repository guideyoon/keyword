from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import traceback

# Ensure the api directory is in the path for local imports
sys.path.append(os.path.dirname(__file__))

try:
    from naver_service import (
        search_blog, get_api_keys, get_naver_section_order, 
        get_related_keywords, get_keyword_info, get_blog_rank, 
        get_search_volume, get_search_volumes_for_keywords, 
        get_realtime_keywords, search_news, search_shop, 
        search_kin, get_datalab_shopping_trends,
        get_related_keywords_from_ad_api, get_google_trending_keywords,
        analyze_top_blogs
    )
except ImportError as e:
    print(f"Import Error: {e}")
    # We will handle this in the routes if needed

import re
import email.utils
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend interaction

@app.route('/api/health')
def health():
    return jsonify(status="ok", message="API is running", python_version=sys.version)

@app.route('/api/debug/ad')
def debug_ad():
    keyword = request.args.get('q', '로봇청소기')
    return jsonify(get_search_volume(keyword))

@app.route('/api/debug')
def debug():
    return jsonify({
        "cwd": os.getcwd(),
        "files": os.listdir(os.path.dirname(__file__)),
        "path": sys.path,
        "env_keys": {
            "NAVER_AD_ACCESS_LICENSE": bool(os.getenv("NAVER_AD_ACCESS_LICENSE")),
            "NAVER_AD_CUSTOMER_ID": bool(os.getenv("NAVER_AD_CUSTOMER_ID"))
        }
    })

def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

@app.route('/api/config', methods=['GET'])
def get_config():
    client_id, client_secret = get_api_keys()
    ad_license = os.getenv("NAVER_AD_ACCESS_LICENSE", "").strip()
    ad_secret = os.getenv("NAVER_AD_SECRET_KEY", "").strip()
    ad_customer = os.getenv("NAVER_AD_CUSTOMER_ID", "").strip()
    
    return jsonify({
        "search_api": {
            "configured": bool(client_id and client_secret),
            "client_id_exists": bool(client_id),
            "client_secret_exists": bool(client_secret)
        },
        "ad_api": {
            "configured": bool(ad_license and ad_secret and ad_customer),
            "license_exists": bool(ad_license),
            "secret_exists": bool(ad_secret),
            "customer_exists": bool(ad_customer)
        },
        "overall_ready": bool(client_id and client_secret and ad_license and ad_secret and ad_customer)
    })

@app.route('/api/realtime', methods=['GET'])
def realtime():
    keywords = get_realtime_keywords()
    return jsonify(keywords)

@app.route('/api/analyze', methods=['GET'])
def analyze():
    keyword = request.args.get('q', '')
    if not keyword:
        return jsonify({"error": "Keyword is required"}), 400
    
    # 1. Basic Blog Search & Summary
    blog_result = search_blog(keyword)
    total_count = blog_result.get('total', 0)
    
    vol_data = get_search_volume(keyword)
    
    # 2. Section Order
    section_orders = get_naver_section_order(keyword)
    
    # 3. Blog Rank
    ranks = get_blog_rank(keyword)
    
    client_id, client_secret = get_api_keys()
    
    return jsonify({
        "keyword": keyword,
        "api_status": {
            "naver_search": bool(client_id and client_secret),
            "naver_ad": bool(os.getenv("NAVER_AD_ACCESS_LICENSE"))
        },
        "summary": {
            "pc": vol_data['pc'] if vol_data else 0,
            "mobile": vol_data['mobile'] if vol_data else 0,
            "total_vol": vol_data['total'] if vol_data else 0,
            "doc_count": total_count,
            "ratio": (total_count / vol_data['total']) if vol_data and vol_data['total'] > 0 else 0
        },
        "sections": section_orders,
        "blog_ranks": ranks
    })

@app.route('/api/related', methods=['GET'])
def related():
    keyword = request.args.get('q', '')
    if not keyword:
        return jsonify({"error": "Keyword is required"}), 400
    
    # Use the Ad API to get related keywords and their volumes directly
    # This is much more accurate than scraping for multi-word queries
    ad_results = get_related_keywords_from_ad_api(keyword)
    if not ad_results:
        return jsonify([])
        
    stat_data = []
    
    # Fetch document counts in parallel to speed up the response
    def fetch_stat(item):
        kwd = item['keyword']
        info = get_keyword_info(kwd)
        docs = info.get('total', 0)
        total_vol = item['total']
        ratio = (docs / total_vol) if total_vol > 0 else 0
        
        return {
            "keyword": kwd,
            "pc": item['pc'],
            "mobile": item['mobile'],
            "total": total_vol,
            "docs": docs,
            "ratio": round(ratio, 4)
        }

    with ThreadPoolExecutor(max_workers=10) as executor:
        # Sort by total volume and take top 30 for better performance and relevance
        top_items = sorted(ad_results, key=lambda x: x['total'], reverse=True)[:30]
        futures = [executor.submit(fetch_stat, item) for item in top_items]
        for future in futures:
            try:
                res = future.result()
                if res['keyword'] != keyword: # Filter out original keyword
                    stat_data.append(res)
            except Exception as e:
                print(f"Error fetching stats for related keyword: {e}")
                
    # Re-sort by total volume for final output
    stat_data.sort(key=lambda x: x['total'], reverse=True)
    return jsonify(stat_data)

@app.route('/api/search', methods=['GET'])
def search():
    keyword = request.args.get('q', '')
    stype = request.args.get('type', 'blog') # blog, news, shop, kin
    
    if not keyword:
        return jsonify({"error": "Keyword is required"}), 400
    
    if stype == 'blog':
        res = search_blog(keyword)
    elif stype == 'news':
        res = search_news(keyword)
    elif stype == 'shop':
        res = search_shop(keyword)
    elif stype == 'kin':
        res = search_kin(keyword)
    else:
        return jsonify({"error": "Invalid search type"}), 400
        
    # Clean data
    items = res.get('items', [])
    cleaned_items = []
    for item in items:
        cleaned_item = {k: remove_html_tags(str(v)) if isinstance(v, str) else v for k, v in item.items()}
        cleaned_items.append(cleaned_item)
        
    return jsonify(cleaned_items)

@app.route('/api/trends/shopping', methods=['GET'])
def shopping_trends():
    cid = request.args.get('cid', '50000000')
    trends = get_datalab_shopping_trends(cid)
    
    if not trends:
        return jsonify([])
        
    keywords = [t['keyword'] for t in trends]
    vol_map = get_search_volumes_for_keywords(keywords)
    
    shop_trend_data = []
    for t in trends:
        kwd = t['keyword']
        vol_info = vol_map.get(kwd.replace(" ", ""), {})
        total_vol = vol_info.get('total', 0)
        
        info = get_keyword_info(kwd)
        doc_count = info.get('total', 0)
        
        ratio = (doc_count / total_vol) if total_vol > 0 else 999
        
        insight = "💎 블루오션" if doc_count < 1000 and total_vol > 10000 else \
                  "✨ 해볼만함" if doc_count < 5000 and total_vol > 5000 else "🔥 레드오션"
            
        shop_trend_data.append({
            "rank": t['rank'],
            "keyword": kwd,
            "volume": total_vol,
            "docs": doc_count,
            "ratio": round(ratio, 4),
            "insight": insight
        })
        
    return jsonify(shop_trend_data)

@app.route('/api/difficulty', methods=['GET'])
def get_difficulty():
    """
    키워드의 상위노출 난이도를 분석합니다.
    상위 블로그들의 콘텐츠 길이, 최신성을 기반으로 점수를 산출합니다.
    """
    keyword = request.args.get('q', '')
    if not keyword:
        return jsonify({'error': '키워드를 입력해주세요'}), 400
    
    result = analyze_top_blogs(keyword, count=5)
    return jsonify(result)

@app.route('/api/gold/discover', methods=['GET'])
def gold_discover():
    try:
        # Ignore user input, strictly use Popular/Trending sources
        user_seed = request.args.get('q', '')
        seed = user_seed # For compatibility with existing logic
        print(f"Popular Discovery requested. (User input '{seed}' ignored)")
        
        candidates = set()
        realtime_set = set()  # Track which keywords are from realtime/trending sources
        
        # 1. Realtime/Trending Keywords
        try:
            realtime = get_realtime_keywords()
            if realtime:
                print(f"Source: Naver Realtime ({len(realtime)})")
                for kw in realtime:
                    candidates.add(kw['keyword'])
                    realtime_set.add(kw['keyword'])  # Mark as trending
        except Exception as e:
            print(f"Realtime fetch error: {e}")

        try:
            google_trends = get_google_trending_keywords(limit=20)
            if google_trends:
                print(f"Source: Google Trends ({len(google_trends)})")
                for kw in google_trends:
                    candidates.add(kw['keyword'])
                    realtime_set.add(kw['keyword'])  # Mark as trending
        except Exception as e:
            print(f"Google trends fetch error: {e}")

        # 2. Broad Popular Seeds (The "Big Net" Strategy)
        POPULAR_SEEDS = [
            "인기검색어", "베스트셀러", "요즘뜨는것", "선물추천", 
            "가볼만한곳", "데이트코스", "축제", "전시회", "캠핑",
            "점심메뉴", "반찬", "간식", "야식",
            "편의점신상", "다이소꿀템", "올리브영추천" 
        ]
        
        # Fetch related keywords for each broad seed
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Helper to fetch ad keywords
            def fetch_ad_candidates(seed):
                try:
                    return get_related_keywords_from_ad_api(seed)
                except:
                    return []

            futures = [executor.submit(fetch_ad_candidates, s) for s in POPULAR_SEEDS]
            for future in futures:
                items = future.result()
                if items:
                    # Take top 20 by volume from each seed
                    # Filter: Volume >= 1000 to ensure quality candidates
                    sorted_items = sorted(items, key=lambda x: x.get('total', 0), reverse=True)
                    for item in sorted_items[:20]:
                        if item.get('total', 0) >= 1000:
                            candidates.add(item['keyword'])
                            
        print(f"Total unique candidates collected: {len(candidates)}")
        
        if not candidates:
            return jsonify([])

        # 3. Analyze Candidates (Limit to top 100 for performance)
        candidate_list = list(candidates)[:100]
        print(f"Total unique candidates to analyze: {len(candidate_list)}")
        vol_map = get_search_volumes_for_keywords(candidate_list)
        print(f"Volume map received for {len(vol_map)} keywords")
        
        # 3. Filter candidates with HIGH volume (1000+ total) - First stage filter
        qualified_candidates = []
        for kwd in candidate_list:
            kwd_key = kwd.replace(" ", "")
            vol_info = vol_map.get(kwd_key, {})
            total_vol = vol_info.get('total', 0)
            pc_vol = vol_info.get('pc', 0)
            mo_vol = vol_info.get('mobile', 0)
            
            # STRICT: Only include keywords with HIGH search volume (1000+)
            if total_vol >= 1000 and (pc_vol > 0 or mo_vol > 0):
                qualified_candidates.append((kwd, vol_info))
                print(f"  ✓ Qualified: {kwd} (PC:{pc_vol}, Mobile:{mo_vol}, Total:{total_vol})")
            else:
                print(f"  ✗ Skipped (low vol): {kwd} -> Total:{total_vol}")

        # 4. Fetch documentation counts in parallel
        def fetch_full_info(kwd, vol_info):
            try:
                vol = vol_info.get('total', 0)
                pc_vol = vol_info.get('pc', 0)
                mo_vol = vol_info.get('mobile', 0)
                comp_idx = vol_info.get('comp_idx', 0)
                
                info = get_keyword_info(kwd)
                doc_count = info.get('total', 0)
                score = vol / (doc_count + 1)
                
                # Identify Primary Platform (Try to get it, but don't fail if it hangs)
                primary_platform = "-"
                try:
                    sections = get_naver_section_order(kwd)
                    # Correctly access the first section from mobile preferences
                    mo_sections = sections.get('mobile', [])
                    if mo_sections:
                        primary_platform = mo_sections[0]
                except Exception as ex:
                    print(f"Platform analysis failed for {kwd}: {ex}")
                
                # Map Competition Index to Label
                if isinstance(comp_idx, (int, float)):
                    if comp_idx < 30: comp_label = "낮음"
                    elif comp_idx < 70: comp_label = "중간"
                    else: comp_label = "높음"
                else:
                    comp_label = str(comp_idx)

                # STRICT Tier Definitions - Only truly golden keywords get good labels
                if doc_count < 1000 and score >= 5.0:
                    label, tier = "💎 종결", "ultra"
                elif doc_count < 5000 and score >= 1.0:
                    label, tier = "🏆 황금", "golden"
                elif doc_count < 20000 and score >= 0.3:
                    label, tier = "✅ 추천", "good"
                else:
                    label, tier = "평범", "normal"
                    
                # Determine trend signal based on realtime membership
                if kwd in realtime_set:
                    trend_signal = "🚀 급상승"
                else:
                    trend_signal = "➡️ 안정"
                    
                return {
                    "rank": "-",
                    "keyword": kwd,
                    "volume": vol,
                    "pc_vol": pc_vol,
                    "mo_vol": mo_vol,
                    "docs": doc_count,
                    "score": round(score, 2),
                    "label": label,
                    "tier": tier,
                    "comp": comp_label,
                    "platform": primary_platform,
                    "trend": trend_signal
                }
            except Exception as e:
                print(f"Error in fetch_full_info for {kwd}: {e}")
                return None

        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Use vol_info directly from qualified_candidates tuple
            future_to_kwd = [executor.submit(fetch_full_info, kwd, vol_info) 
                             for kwd, vol_info in qualified_candidates]
            for future in future_to_kwd:
                try:
                    res = future.result()
                    # STRICT FILTERS: Only truly golden keywords pass through
                    # 1. Not the seed keyword
                    # 2. Score >= 0.1 (high volume / docs ratio)
                    # 3. Docs <= 50,000 (low competition market)
                    if res and res['keyword'] != seed and res['score'] >= 0.1 and res['docs'] <= 50000: 
                        results.append(res)
                        print(f"  ★ Golden Found: {res['keyword']} (Score:{res['score']}, Docs:{res['docs']})")
                    elif res:
                        print(f"  ✗ Filtered out: {res['keyword']} (Score:{res['score']}, Docs:{res['docs']})")
                except Exception as e:
                    print(f"Error fetching docs: {e}")
        
        # Sort by score descending before checking count
        results.sort(key=lambda x: x['score'], reverse=True)
        print(f"Discovery complete. Found {len(results)} TRUE golden keywords.")
        
        if len(results) < 5:
            print("Results < 5, but fallback logic is deprecated for Popular Discovery mode.")
            


        # 5. Final Sort by Score (Volume/Docs) Descending
        results.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"Discovery complete. Found {len(results)} items.")
        return jsonify(results[:20]) # Return top 20
    except Exception as e:
        print(f"ERROR in gold_discover: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
