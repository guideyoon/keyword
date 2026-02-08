const API_BASE = "/api";
let currentKeyword = "";
let currentTab = "blog";
let adsenseShown = false;

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initSearch();
    initTabs();
    initTheme();
    initMobileMenu();
    loadRealtime();
});

// Show AdSense container only after content is loaded
function showAdsenseAd() {
    if (adsenseShown) return;
    const adContainer = document.getElementById('adsense-container');
    if (adContainer) {
        adContainer.style.display = 'block';
        adsenseShown = true;
    }
}

function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const tab = item.getAttribute('data-tab');

            // UI state
            navItems.forEach(n => n.classList.remove('active'));
            item.classList.add('active');

            // View state
            document.querySelectorAll('.view-content').forEach(view => {
                view.classList.remove('active');
            });
            document.getElementById(`${tab}-view`).classList.add('active');

            if (tab === 'realtime') loadRealtime();
            if (tab === 'shopping') initShopping();
            if (tab === 'gold') initGold();
        });
    });
}

function navigateTo(tabName) {
    const navItems = document.querySelectorAll('.nav-item');
    const targetItem = Array.from(navItems).find(i => i.getAttribute('data-tab') === tabName);

    if (targetItem) {
        navItems.forEach(n => n.classList.remove('active'));
        targetItem.classList.add('active');

        document.querySelectorAll('.view-content').forEach(view => {
            view.classList.remove('active');
        });
        document.getElementById(`${tabName}-view`).classList.add('active');

        if (tabName === 'realtime') loadRealtime();
        if (tabName === 'shopping') initShopping();
        if (tabName === 'gold') loadGoldKeywords();
    }
}

function initSearch() {
    const input = document.getElementById('keyword-input');
    const btn = document.getElementById('search-btn');

    btn.addEventListener('click', () => {
        const kwd = input.value.trim();
        if (kwd) performAnalysis(kwd);
    });

    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const kwd = input.value.trim();
            if (kwd) performAnalysis(kwd);
        }
    });
}

function initTabs() {
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentTab = tab.getAttribute('data-type');
            if (currentKeyword) loadSearchResults(currentKeyword, currentTab);
        });
    });
}

function initTheme() {
    const toggle = document.getElementById('theme-toggle');
    const icon = toggle.querySelector('i');

    // Check saved theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        icon.className = 'fas fa-sun';
    }

    toggle.addEventListener('click', () => {
        const isDark = document.body.classList.toggle('dark-mode');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        icon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';

        showToast(isDark ? '다크 모드 활성화' : '라이트 모드 활성화');
    });
}

async function performAnalysis(keyword) {
    currentKeyword = keyword;
    const btn = document.getElementById('search-btn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 분석 중...';

    try {
        const response = await fetch(`${API_BASE}/analyze?q=${encodeURIComponent(keyword)}`);
        const data = await response.json();

        if (data.error) {
            showToast(data.error, 'error');
            return;
        }

        // Hide welcome guide and show stats on first search
        const welcomeGuide = document.getElementById('welcome-guide');
        if (welcomeGuide) {
            welcomeGuide.style.display = 'none';
        }

        updateStats(data.summary);
        updateSections(data.sections);
        loadSearchResults(keyword, currentTab);
        loadRelatedKeywords(keyword);

        // Fetch difficulty score
        try {
            const diffRes = await fetch(`${API_BASE}/difficulty?q=${encodeURIComponent(keyword)}`);
            const diffData = await diffRes.json();
            if (!diffData.error) {
                document.getElementById('difficulty-score').textContent = diffData.difficulty_score + '점';
                document.getElementById('difficulty-label').textContent = diffData.difficulty;

                // Color code the difficulty card
                const diffCard = document.getElementById('difficulty-card');
                diffCard.classList.remove('easy', 'medium', 'hard');
                if (diffData.difficulty_score < 30) {
                    diffCard.classList.add('easy');
                } else if (diffData.difficulty_score < 60) {
                    diffCard.classList.add('medium');
                } else {
                    diffCard.classList.add('hard');
                }
            }
        } catch (diffErr) {
            console.log('Difficulty fetch error:', diffErr);
        }

        showToast(`'${keyword}' 분석 완료`, 'success');
        showAdsenseAd();

    } catch (err) {
        showToast("분석 중 오류가 발생했습니다.", "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-search"></i> 분석하기';
    }
}

function updateStats(summary) {
    document.getElementById('pc-vol').innerText = summary.pc.toLocaleString();
    document.getElementById('mo-vol').innerText = summary.mobile.toLocaleString();
    document.getElementById('total-vol').innerText = summary.total_vol.toLocaleString();
    document.getElementById('doc-count').innerText = summary.doc_count.toLocaleString();
    document.getElementById('ratio').innerText = summary.ratio.toFixed(4);

    // Status text based on ratio
    const docStatus = document.getElementById('doc-status');
    if (summary.ratio < 0.1) {
        docStatus.innerText = "💎 블루오션";
        docStatus.className = "stat-change up";
    } else if (summary.ratio < 0.5) {
        docStatus.innerText = "✨ 경쟁적당";
        docStatus.className = "stat-change down";
        docStatus.style.color = "var(--blue)";
    } else {
        docStatus.innerText = "🔥 레드오션";
        docStatus.className = "stat-change down";
    }

    // Bar update
    const bar = document.querySelector('.progress-bar');
    const displayRatio = Math.min((summary.total_vol / 100000) * 100, 100);
    bar.style.width = `${displayRatio}%`;
}

function updateSections(sections) {
    const pcList = document.getElementById('pc-sections-mini');
    const moList = document.getElementById('mo-sections-mini');

    if (pcList) pcList.innerHTML = sections.pc.length > 0 ? sections.pc.slice(0, 3).map((s, i) => `<li>${i + 1}. ${s}</li>`).join('') : '<li>-</li>';
    if (moList) moList.innerHTML = sections.mobile.length > 0 ? sections.mobile.slice(0, 3).map((s, i) => `<li>${i + 1}. ${s}</li>`).join('') : '<li>-</li>';
}

async function loadRelatedKeywords(keyword) {
    const container = document.getElementById('related-keywords-container');
    container.innerHTML = '<div class="loading-spinner">연관 키워드 분석 중...</div>';

    try {
        const response = await fetch(`${API_BASE}/related?q=${encodeURIComponent(keyword)}`);
        const data = await response.json();

        if (!data || data.length === 0) {
            container.innerHTML = '<div class="loading-spinner">연관 키워드가 없습니다.</div>';
            return;
        }

        container.innerHTML = data.map(item => `
            <div class="related-item" onclick="document.getElementById('keyword-input').value='${item.keyword}'; performAnalysis('${item.keyword}'); navigateTo('dashboard')">
                <span class="related-kwd-name">${item.keyword}</span>
                <div class="related-kwd-stats">
                    <span>조회 <b>${item.total.toLocaleString()}</b></span>
                    <span>문서 <b>${item.docs.toLocaleString()}</b></span>
                </div>
                <div class="related-kwd-stats" style="margin-top: 4px;">
                    <span>비율 <b>${item.ratio.toFixed(2)}</b></span>
                </div>
            </div>
        `).join('');

    } catch (err) {
        container.innerHTML = '<div class="loading-spinner">연관 키워드 로드 실패</div>';
    }
}

async function loadSearchResults(keyword, type) {
    const container = document.getElementById('results-table');
    container.innerHTML = '<div class="loading-spinner">데이터 로드 중...</div>';

    try {
        const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(keyword)}&type=${type}`);
        const items = await response.json();

        if (items.length === 0) {
            container.innerHTML = '<div class="loading-spinner">결과가 없습니다.</div>';
            return;
        }

        container.innerHTML = items.map(item => `
            <div class="item-row clickable-result" onclick="window.open('${item.link}', '_blank')" style="cursor: pointer;">
                <div class="item-title">${item.title || item.bloggername || '결과'}</div>
                <div class="item-desc">${item.description || (item.lprice ? item.lprice + '원' : '') || ''}</div>
                <div class="item-meta" style="font-size: 11px; margin-top: 8px; color: #64748b;">
                    ${item.bloggername || item.mallName || ''} ${item.postdate ? '| ' + item.postdate : ''}
                    <span style="float: right; color: var(--accent);"><i class="fas fa-external-link-alt"></i> 원문보기</span>
                </div>
            </div>
        `).join('');

    } catch (err) {
        container.innerHTML = '<div class="loading-spinner">에러가 발생했습니다.</div>';
    }
}

async function loadRealtime() {
    const container = document.getElementById('realtime-keywords');
    container.innerHTML = '<div class="loading-spinner">실시간 정보를 가져오는 중...</div>';

    try {
        const response = await fetch(`${API_BASE}/realtime`);
        const keywords = await response.json();

        container.innerHTML = keywords.map(k => `
            <div class="item-row" style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; gap: 12px; align-items: center;">
                    <span style="color: var(--accent); font-weight: 700; width: 24px;">${k.rank}</span>
                    <span style="font-weight: 600;">${k.keyword}</span>
                </div>
                <span class="stat-change ${k.change === '+' ? 'up' : k.change === '-' ? 'down' : ''}">
                    ${k.change === '+' ? '🔺' : k.change === '-' ? '🔻' : '•'}
                </span>
            </div>
        `).join('');
        showAdsenseAd();
    } catch (err) {
        container.innerHTML = '<div class="loading-spinner">에러가 발생했습니다.</div>';
    }
}

function initShopping() {
    const btn = document.getElementById('shop-refresh-btn');
    btn.onclick = loadShoppingTrends;
}

async function loadShoppingTrends() {
    const cid = document.getElementById('shop-category').value;
    const container = document.getElementById('shopping-trends-container');
    container.innerHTML = '<div class="loading-spinner">쇼핑 트렌드 채굴 중... (약 10초 소요)</div>';

    try {
        const response = await fetch(`${API_BASE}/trends/shopping?cid=${cid}`);
        const data = await response.json();

        if (data.length === 0) {
            container.innerHTML = '<div class="loading-spinner">데이터가 없습니다.</div>';
            return;
        }

        container.innerHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>순위</th><th>키워드</th><th>검색량</th><th>문서수</th><th>비율</th><th>분석</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.map(item => `
                        <tr>
                            <td>${item.rank}</td>
                            <td class="clickable" onclick="document.getElementById('keyword-input').value='${item.keyword}'; performAnalysis('${item.keyword}'); navigateTo('dashboard')"><b>${item.keyword}</b></td>
                            <td>${item.volume.toLocaleString()}</td>
                            <td>${item.docs.toLocaleString()}</td>
                            <td>${item.ratio.toFixed(4)}</td>
                            <td><span class="badge ${item.insight.includes('블루') ? 'success' : 'info'}">${item.insight}</span></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        showAdsenseAd();
    } catch (err) {
        container.innerHTML = '<div class="loading-spinner">로드 실패</div>';
    }
}

function initGold() {
    const btn = document.getElementById('gold-discover-btn');
    if (btn) btn.onclick = loadGoldKeywords;
}

async function loadGoldKeywords() {
    const container = document.getElementById('gold-keywords-container');
    const btn = document.getElementById('gold-discover-btn');
    const seed = document.getElementById('keyword-input').value || '인기아이템';

    container.innerHTML = '<div class="loading-spinner">네이버 연관 검색 데이터 분석 중... (약 15초 소요)</div>';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 분석 중...';
    }

    try {
        const response = await fetch(`${API_BASE}/gold/discover?q=${encodeURIComponent(seed)}`);
        let data = await response.json();

        if (!data || data.length === 0) {
            container.innerHTML = '<div class="loading-spinner">데이터가 없습니다.</div>';
            return;
        }

        // Sort by Golden Score descending (Higher is better: High Volume, Low Docs)
        data.sort((a, b) => b.score - a.score);

        container.innerHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>순위</th><th>키워드</th><th>트렌드</th><th>PC/모바일</th><th>문서수</th><th>황금점수</th><th>경쟁도</th><th>상태</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.map(item => `
                        <tr>
                            <td>${item.rank || '-'}</td>
                            <td class="clickable" onclick="document.getElementById('keyword-input').value='${item.keyword}'; performAnalysis('${item.keyword}'); navigateTo('dashboard')"><b>${item.keyword}</b></td>
                            <td><span class="trend-chip ${item.trend && item.trend.includes('급상승') ? 'trending' : 'stable'}">${item.trend || '➡️'}</span></td>
                            <td>
                                <div style="font-size: 0.85em;">
                                    <span style="color:var(--primary)">${(item.pc_vol || 0).toLocaleString()}</span> / 
                                    <span style="color:var(--secondary)">${(item.mo_vol || 0).toLocaleString()}</span>
                                </div>
                            </td>
                            <td>${(item.docs || 0).toLocaleString()}</td>
                            <td>${(item.score || 0).toFixed(2)}</td>
                            <td><span class="badge comp-${item.comp === '높음' ? 'high' : (item.comp === '중간' ? 'mid' : 'low')}">${item.comp || '-'}</span></td>
                            <td><span class="badge ${item.tier || 'info'}">${item.label || '평범'}</span></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (err) {
        console.error('Golden Keyword Error:', err);
        container.innerHTML = '<div class="loading-spinner">분석 실패: ' + err.message + '</div>';
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-search-plus"></i> 황금 키워드 채굴 시작';
        }
    }
}

function showToast(msg, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerText = msg;

    // Add toast styles if not already in CSS
    if (!document.getElementById('toast-style')) {
        const style = document.createElement('style');
        style.id = 'toast-style';
        style.innerHTML = `
            #toast-container { position: fixed; bottom: 24px; right: 24px; display: flex; flex-direction: column; gap: 8px; z-index: 1000; }
            .toast { padding: 12px 24px; background: #1e293b; border: 1px solid var(--border); border-radius: 10px; color: white; font-size: 14px; animation: slideIn 0.3s ease; }
            .toast.success { border-bottom: 2px solid var(--green); }
            .toast.error { border-bottom: 2px solid var(--red); }
            @keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }
        `;
        document.head.appendChild(style);
    }

    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function initMobileMenu() {
    const toggle = document.getElementById('mobile-menu-toggle');
    const overlay = document.getElementById('sidebar-overlay');
    const appContainer = document.querySelector('.app-container');
    const navItems = document.querySelectorAll('.nav-item');

    if (toggle) {
        toggle.addEventListener('click', () => {
            appContainer.classList.toggle('sidebar-open');
        });
    }

    if (overlay) {
        overlay.addEventListener('click', () => {
            appContainer.classList.remove('sidebar-open');
        });
    }

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            appContainer.classList.remove('sidebar-open');
        });
    });
}
