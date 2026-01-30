import streamlit as st
import pandas as pd
from naver_service import search_blog, get_api_keys, get_naver_section_order, get_related_keywords, get_keyword_info, get_blog_rank, get_search_volume, get_search_volumes_for_keywords, get_realtime_keywords, search_news, search_shop, search_kin, get_datalab_shopping_trends
from datetime import datetime
from datetime import datetime
import re
from dotenv import load_dotenv
import email.utils

load_dotenv()

# 페이지 설정
st.set_page_config(page_title="네이버 키워드 분석기", page_icon="🔍", layout="wide")

# 제목 및 설명
st.title("🔍 네이버 키워드 분석기")
st.markdown("""
키워드를 입력하면 네이버 블로그 검색 결과를 분석해드립니다.
**총 문서 수(발행량)**와 **상위 노출 블로그**를 확인할 수 있습니다.
""")

# 사이드바 설정
with st.sidebar:
    st.header("설정")
    client_id, client_secret = get_api_keys()
    
    if not client_id or not client_secret:
        st.error("⚠️ API 키가 설정되지 않았습니다.")
        st.info("프로젝트 폴더의 `.env` 파일에 네이버 Client ID와 Secret을 입력해주세요.")
        st.markdown("[네이버 개발자 센터 바로가기](https://developers.naver.com/apps/#/register)")
    else:
        st.success("API 키가 로드되었습니다.")
        
    st.markdown("---")
    sort_option = st.radio("정렬 기준", ("정확도순 (sim)", "최신순 (date)"), index=0)
    sort_code = 'sim' if '정확도' in sort_option else 'date'

    st.markdown("---")
    st.subheader("🔥 실시간 급상승 (Nate)")
    
    if st.button("새로고침"):
        st.rerun()
        
    realtime_keywords = get_realtime_keywords()
    if realtime_keywords:
        for item in realtime_keywords:
            rank = item['rank']
            kwd = item['keyword']
            change = item['change']
            
            # Change indicator
            if change == '+':
                change_icon = "🔺"
            elif change == '-':
                change_icon = "🔻"
            elif change == 'n':
                change_icon = "🆕"
            else:
                change_icon = "-"
                
            st.markdown(f"**{rank}위** {kwd} <span style='color:grey; font-size:0.8em'>{change_icon}</span>", unsafe_allow_html=True)
            
            # Click to search (optional UX improvement)
            # if st.button(f"{kwd} 분석", key=f"rt_{rank}"):
            #     st.query_params["q"] = kwd
            #     st.rerun()
    else:
        st.info("실시간 검색어를 가져올 수 없습니다.")

# ... (Imports remain same)

# 함수화: 상단 요약 바 표시
def draw_summary_bar(keyword, total_count_override=None):
    st.markdown(f"### 📈 키워드 종합 분석: **{keyword}**")
    
    # 검색량 조회
    with st.spinner(f"'{keyword}' 검색 데이터 조회 중..."):
        vol_data = get_search_volume(keyword)
    
    # 문서수 조회 (만약 override가 없으면 직접 조회)
    if total_count_override is None:
        info = get_keyword_info(keyword)
        doc_count = info.get('total', 0)
    else:
        doc_count = total_count_override

    pc_vol = vol_data['pc'] if vol_data else 0
    mo_vol = vol_data['mobile'] if vol_data else 0
    total_vol = vol_data['total'] if vol_data else 0
    
    ratio = (doc_count / total_vol) if total_vol > 0 else 0
    
    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
    
    with m_col1:
        st.metric("PC 검색량", f"{pc_vol:,}" if vol_data else "-")
    with m_col2:
        st.metric("모바일 검색량", f"{mo_vol:,}" if vol_data else "-")
    with m_col3:
        st.metric("총 조회수", f"{total_vol:,}" if vol_data else "-")
    with m_col4:
        st.metric("문서수 (블로그)", f"{doc_count:,}")
    with m_col5:
        st.metric("비율 (문서/조회)", f"{ratio:.2f}" if vol_data else "-")
    
    if not vol_data:
        st.caption("※ 네이버 검색광고 API 연동 실패 또는 검색량이 0입니다.")
    
    st.markdown("---")



@st.cache_data(ttl=3600)
def get_cached_related_data(keyword):
    related_keywords = get_related_keywords(keyword)
    if not related_keywords:
        return None, []
        
    # Batch fetch volume for these specific keywords
    ad_vol_dict = get_search_volumes_for_keywords(related_keywords)
    stat_data = []
    
    for r_kwd in related_keywords:
        vol_info = ad_vol_dict.get(r_kwd.replace(" ", ""), None)
        
        if vol_info:
            r_pc = vol_info['pc']
            r_mo = vol_info['mobile']
            r_total = vol_info['total']
        else:
            r_pc = 0
            r_mo = 0
            r_total = 0
        
        info = get_keyword_info(r_kwd)
        r_docs = info.get('total', 0)
        
        r_ratio = (r_docs / r_total) if r_total > 0 else 0
        
        stat_data.append({
            "키워드": r_kwd,
            "PC 검색량": r_pc,
            "모바일 검색량": r_mo,
            "총 조회수": r_total,
            "문서수 (블로그)": r_docs,
            "비율 (문서/조회)": round(r_ratio, 2)
        })
        
    return related_keywords, stat_data

# HTML 태그 제거 함수
def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

# 쿼리 파라미터 처리
if "q" in st.query_params:
    default_keyword = st.query_params["q"]
else:
    default_keyword = ""

# 메인 입력
if "sub_keyword" not in st.session_state:
    st.session_state["sub_keyword"] = None

keyword = st.text_input("분석할 키워드를 입력하세요", value=default_keyword, placeholder="예: 강남 맛집, 로봇청소기 추천")


# 탭 생성 (항상 표시)
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 종합 분석", "📝 블로그", "📰 뉴스", "🛍️ 쇼핑", "❓ 지식iN", "💎 황금 키워드"])

if keyword:
    # Reset sub keyword on new search
    if "last_main_keyword" not in st.session_state or st.session_state["last_main_keyword"] != keyword:
         st.session_state["sub_keyword"] = None
         st.session_state["last_main_keyword"] = keyword

    # [TAB 1] 종합 분석
    with tab1:
        with st.spinner(f"'{keyword}' 기본 데이터 분석 중..."):
            # 기본 블로그 검색 (문서수 확인용)
            blog_result = search_blog(keyword, sort=sort_code)
            total_count = blog_result.get('total', 0)
            
            # 1. 메인 키워드 요약
            draw_summary_bar(keyword, total_count_override=total_count)
            
            # 2. 섹션 순서 분석
            st.markdown("### 📊 섹션 배치 순서")
            section_orders = get_naver_section_order(keyword)
            
            sec_col1, sec_col2 = st.columns(2)
            with sec_col1:
                st.markdown("#### 🖥️ PC 검색 결과")
                if section_orders['pc']:
                    for idx, section in enumerate(section_orders['pc'], 1):
                        # 블로그 섹션에는 별표 추가
                        display_section = f"{section} ⭐" if "블로그" in section else section
                        st.write(f"{idx}. {display_section}")
                else:
                    st.info("섹션 정보를 찾을 수 없습니다.")

            with sec_col2:
                st.markdown("#### 📱 모바일 검색 결과")
                if section_orders['mobile']:
                    for idx, section in enumerate(section_orders['mobile'], 1):
                        # 블로그 섹션에는 별표 추가
                        display_section = f"{section} ⭐" if "블로그" in section else section
                        st.write(f"{idx}. {display_section}")
                else:
                    st.info("섹션 정보를 찾을 수 없습니다.")

            st.markdown("---")

            # 3. 연관 키워드 분석
            st.subheader("🔗 연관 키워드 분석 결과")
            
            # 여기서 캐시된 함수를 호출하지만, keyword가 있을 때만 실행됨
            related_keywords, stat_data = get_cached_related_data(keyword)
            
            if related_keywords:
                kwd_df = pd.DataFrame(stat_data)
                st.dataframe(
                    kwd_df,
                    column_config={
                        "PC 검색량": st.column_config.NumberColumn(format="%d"),
                        "모바일 검색량": st.column_config.NumberColumn(format="%d"),
                        "총 조회수": st.column_config.NumberColumn(format="%d"),
                        "문서수 (블로그)": st.column_config.NumberColumn(format="%d"),
                        "비율 (문서/조회)": st.column_config.NumberColumn(format="%.2f"),
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
                # 상세 분석 선택
                st.markdown("##### 📌 개별 키워드 상세 리포트 확인")
                
                idx = 0
                if st.session_state.get("sub_keyword") in related_keywords:
                    idx = related_keywords.index(st.session_state["sub_keyword"]) + 1
                    
                selected_kwd = st.selectbox(
                    "분석할 키워드를 선택하세요", 
                    ["선택안함"] + related_keywords,
                    index=idx
                )
                
                if selected_kwd != "선택안함":
                    st.session_state["sub_keyword"] = selected_kwd
                else:
                        st.session_state["sub_keyword"] = None
            else:
                st.info("연관 키워드를 찾을 수 없습니다.")                
        
        # [Sub Keyword Analysis]
        if st.session_state["sub_keyword"]:
            sub_kwd = st.session_state["sub_keyword"]
            st.markdown("---")
            st.markdown(f"### 🔍 상세 분석: **{sub_kwd}**")
            
            draw_summary_bar(sub_kwd)
            
            with st.spinner("블로그 상위 노출 분석 중..."):
                ranks = get_blog_rank(sub_kwd)
                
            st.markdown("#### 📊 VIEW 상위 노출 구성")
            rank_visual = ""
            for r in ranks:
                if r == 'B': rank_visual += "🟩(블로그) "
                elif r == 'C': rank_visual += "🟦(카페) "
                else: rank_visual += "⬜(기타) "
            st.write(rank_visual)
            
            with st.expander(f"'{sub_kwd}' 상위 노출 블로그 보기"):
                sub_res = search_blog(sub_kwd)
                if sub_res and 'items' in sub_res:
                    for s_idx, s_item in enumerate(sub_res['items'], 1):
                        st.write(f"{s_idx}. [{remove_html_tags(s_item['title'])}]({s_item['link']})")

    # [TAB 2] 블로그
    with tab2:
        st.subheader(f"📝 블로그 검색 결과: {keyword}")
        if blog_result and 'items' in blog_result:
            items = blog_result['items']
            data = []
            for item in items:
                data.append({
                    "제목": remove_html_tags(item['title']),
                    "요약": remove_html_tags(item['description']),
                    "블로거": item['bloggername'],
                    "작성일": item['postdate'],
                    "링크": item['link']
                })
            
            df = pd.DataFrame(data)
            st.dataframe(
                df,
                column_config={"링크": st.column_config.LinkColumn("바로가기")},
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("블로그 검색 결과가 없습니다.")

    # [TAB 3] 뉴스
    with tab3:
        st.subheader(f"📰 관련 뉴스: {keyword}")
        with st.spinner("뉴스 검색 중..."):
            news_res = search_news(keyword, display=20)
            if news_res and 'items' in news_res:
                n_items = news_res['items']
                for n_idx, item in enumerate(n_items, 1):
                    title = remove_html_tags(item['title'])
                    desc = remove_html_tags(item['description'])
                    link = item['link']
                    pub_date = item['pubDate']
                    
                    # Date Formatting
                    try:
                        # Parse RFC 2822 date
                        dt = email.utils.parsedate_to_datetime(pub_date)
                        formatted_date = dt.strftime("%Y년 %m월 %d일 %H:%M")
                    except Exception:
                        formatted_date = pub_date

                    st.markdown(f"**{n_idx}. [{title}]({link})**")
                    st.caption(f"{formatted_date} | {desc}")
                    st.markdown("---")
            else:
                st.info("뉴스 검색 결과가 없습니다.")

    # [TAB 4] 쇼핑
    with tab4:
        st.subheader(f"🛍️ 쇼핑 검색 결과: {keyword}")
        with st.spinner("쇼핑 상품 검색 중..."):
            shop_res = search_shop(keyword, display=20)
            if shop_res and 'items' in shop_res:
                s_items = shop_res['items']
                
                # Grid Layout
                cols = st.columns(3)
                for idx, item in enumerate(s_items):
                    with cols[idx % 3]:
                        title = remove_html_tags(item['title'])
                        lprice = item['lprice']
                        link = item['link']
                        image = item['image']
                        mall = item['mallName']
                        
                        st.image(image, use_column_width=True)
                        st.markdown(f"**[{title}]({link})**")
                        st.markdown(f"💰 **{int(lprice):,}원**")
                        st.caption(f"판매처: {mall}")
            else:
                st.info("쇼핑 검색 결과가 없습니다.")

    # [TAB 5] 지식iN
    with tab5:
        st.subheader(f"❓ 지식iN 질문: {keyword}")
        # st.caption("※ 네이버 지식iN 검색 API는 작성일자 정보를 제공하지 않습니다.")
        with st.spinner("지식iN 검색 중..."):
            kin_res = search_kin(keyword, display=20)
            if kin_res and 'items' in kin_res:
                k_items = kin_res['items']
                for item in k_items:
                    title = remove_html_tags(item['title'])
                    desc = remove_html_tags(item['description'])
                    link = item['link']
                    
                    with st.expander(f"Q. {title}"):
                        st.write(desc)
                        st.markdown(f"[답변 보러가기]({link})")
            else:
                st.info("지식iN 검색 결과가 없습니다.")
else:
    # 키워드가 없을 때 안내 메시지 (탭 1~5)
    with tab1: st.info("먼저 분석할 키워드를 입력해주세요.")
    with tab2: st.info("먼저 분석할 키워드를 입력해주세요.")
    with tab3: st.info("먼저 분석할 키워드를 입력해주세요.")
    with tab4: st.info("먼저 분석할 키워드를 입력해주세요.")
    with tab5: st.info("먼저 분석할 키워드를 입력해주세요.")

# [TAB 6] 💎 황금 키워드 (항상 표시)
with tab6:
    st.subheader("💎 황금 키워드 발굴")
    
    # 분석 모드 선택
    analysis_mode = st.radio(
        "분석 모드 선택", 
        ("🎯 연관 키워드 분석 (현재 검색어 기준)", "🔥 실시간 이슈 발굴 (Nate 트렌드 기준)", "🛍️ 쇼핑 트렌드 발굴 (데이터랩 기준)"),
        help="연관 키워드: 입력 키워드 기반 / 실시간 이슈: Nate 급상승 / 쇼핑 트렌드: 분야별 쇼핑 인기 검색어"
    )
    
    st.markdown("---")
    
    if "연관 키워드" in analysis_mode:
        if keyword:
            st.markdown("""
            **황금 키워드란?**  
            검색량은 많지만 문서수(경쟁)는 적은 '알짜' 키워드입니다.  
            점수(Score)가 높을수록 상위 노출 기회가 높습니다. (Score = 총 조회수 / 문서수)
            """)
            
            with st.spinner("황금 키워드 채굴 중..."):
                related_keywords_data, stat_data_local = get_cached_related_data(keyword)
                if related_keywords_data:
                    gold_data = []
                    for item in stat_data_local:
                        total_vol = item['총 조회수']
                        doc_count = item['문서수 (블로그)']
                        
                        if total_vol < 100: continue
                        score = total_vol / (doc_count + 1)
                        gold_data.append({
                            "키워드": item['키워드'],
                            "총 조회수": total_vol,
                            "문서수": doc_count,
                            "황금점수": round(score, 2),
                            "경쟁강도": round(item['비율 (문서/조회)'], 4)
                        })
                    
                    if gold_data:
                        gold_df = pd.DataFrame(gold_data)
                        gold_df = gold_df.sort_values(by="황금점수", ascending=False).reset_index(drop=True)
                        
                        top_cols = st.columns(3)
                        for i in range(min(3, len(gold_df))):
                            row = gold_df.iloc[i]
                            kwd = row['키워드']
                            sc = row['황금점수']
                            medal = ["🥇", "🥈", "🥉"][i]
                            with top_cols[i]:
                                st.success(f"{medal} {kwd}")
                                st.metric("황금점수", sc, delta="추천")
                                st.caption(f"검색 {row['총 조회수']:,} / 문서 {row['문서수']:,}")
                        
                        st.markdown("---")
                        st.dataframe(
                            gold_df,
                            column_config={
                                "황금점수": st.column_config.NumberColumn(format="%.2f"),
                                "총 조회수": st.column_config.NumberColumn(format="%d"),
                                "문서수": st.column_config.NumberColumn(format="%d"),
                                "경쟁강도": st.column_config.ProgressColumn(
                                    "경쟁강도 (낮을수록 좋음)", format="%.4f", min_value=0, max_value=1
                                ),
                            },
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.warning("유효한 데이터가 부족합니다.")
                else:
                    st.info("먼저 메인 키워드를 입력하고 분석을 시작해주세요.")
        else:
            st.info("분석할 키워드를 입력하면 연관 키워드를 분석해드립니다. 실시간 이슈를 찾으려면 위에서 '실시간 이슈 발굴'을 선택하세요.")
                
    elif "쇼핑 트렌드" in analysis_mode:
        st.markdown("### 🛍️ 쇼핑 인기 검색어 (DataLab)")
        st.caption("최근 3일간 네이버 쇼핑에서 가장 많이 검색된 키워드를 분석합니다.")
        
        # Category Mapper
        categories = {
            "패션의류": "50000000",
            "패션잡화": "50000001",
            "화장품/미용": "50000002",
            "디지털/가전": "50000003",
            "가구/인테리어": "50000004",
            "출산/육아": "50000005",
            "식품": "50000006",
            "스포츠/레저": "50000007",
            "생활/건강": "50000008",
            "여가/생활편의": "50000009",
            "면세점": "50000010"
        }
        
        selected_cat = st.selectbox("카테고리 선택", list(categories.keys()))
        cid = categories[selected_cat]
        
        if st.button("쇼핑 트렌드 분석 시작", type="primary"):
            with st.spinner(f"'{selected_cat}' 인기 키워드 수집 및 분석 중..."):
                # 1. Fetch Top 20 Keywords
                trends = get_datalab_shopping_trends(cid)
                
                if trends:
                    keywords = [t['keyword'] for t in trends]
                    
                    # 2. Bulk Fetch Volumes
                    vol_map = get_search_volumes_for_keywords(keywords)
                    
                    shop_trend_data = []
                    for t in trends:
                        kwd = t['keyword']
                        rank = t['rank']
                        
                        # Volume
                        vol_info = vol_map.get(kwd.replace(" ", ""), {})
                        total_vol = vol_info.get('total', 0)
                        
                        # Doc Count
                        info = get_keyword_info(kwd)
                        doc_count = info.get('total', 0)
                        
                        # Score & Insight
                        if total_vol > 0:
                            ratio = doc_count / total_vol
                        else:
                            ratio = 999
                        
                        if doc_count < 1000 and total_vol > 10000:
                            insight = "💎 블루오션 (강추)"
                        elif doc_count < 5000 and total_vol > 5000:
                            insight = "✨ 해볼만함 (추천)"
                        else:
                            insight = "🔥 레드오션 (보통)"
                            
                        shop_trend_data.append({
                            "순위": rank,
                            "키워드": kwd,
                            "검색량": total_vol,
                            "문서수": doc_count,
                            "경쟁도": round(ratio, 4),
                            "분석결과": insight
                        })
                    
                    s_df = pd.DataFrame(shop_trend_data)
                    
                    st.dataframe(
                        s_df,
                        column_config={
                            "검색량": st.column_config.NumberColumn(format="%d"),
                            "문서수": st.column_config.NumberColumn(format="%d"),
                            "경쟁도": st.column_config.ProgressColumn(format="%.4f", min_value=0, max_value=0.5),
                        },
                        use_container_width=True, hide_index=True
                    )
                else:
                    st.error("데이터랩 정보를 가져올 수 없습니다.")

    else: # 실시간 이슈 발굴 모드 (Nate)
        st.markdown("""
        **🔥 실시간 블루오션 찾기**  
        현재 급상승 중인 키워드 중, **아직 블로그 문서가 많이 생성되지 않은** 틈새 시장을 찾습니다.
        """)
        
        if st.button("실시간 트렌드 분석 시작", type="primary"):
            with st.spinner("Nate 실시간 트렌드 및 문서 수 분석 중..."):
                trends = get_realtime_keywords()
                if trends:
                    trend_gold_data = []
                    for idx, item in enumerate(trends):
                        tkwd = item['keyword']
                        rank = item['rank']
                        
                        # 문서수 조회
                        info = get_keyword_info(tkwd)
                        doc_count = info.get('total', 0)
                        
                        # Simple insight tag
                        if doc_count < 100:
                            insight = "💎 블루오션 (선점필수)"
                            color = "green"
                        elif doc_count < 1000:
                            insight = "✨ 해볼만함 (경쟁적당)"
                            color = "blue"
                        else:
                            insight = "🔥 레드오션 (경쟁치열)"
                            color = "red"
                            
                        trend_gold_data.append({
                            "순위": rank,
                            "키워드": tkwd,
                            "문서수": doc_count,
                            "분석결과": insight
                        })
                        
                    t_df = pd.DataFrame(trend_gold_data)
                    
                    st.dataframe(
                        t_df,
                        column_config={
                            "문서수": st.column_config.NumberColumn(format="%d"),
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.error("실시간 트렌드를 가져오는데 실패했습니다.")

