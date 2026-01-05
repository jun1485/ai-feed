"""
블로그 필수 페이지 HTML 템플릿
AdSense 승인을 위한 Privacy Policy, About, Contact 페이지 생성
한국어/영어 페이지를 별도로 관리
"""

from typing import Dict, Callable

# =============================================================================
# 한국어 페이지 (Korean Pages)
# =============================================================================

def get_privacy_policy_ko(blog_name: str = "AI 테크 블로그", blog_url: str = "https://besting2.blogspot.com") -> str:
    """개인정보처리방침 페이지 HTML (한국어)"""
    return f"""
<h2>개인정보처리방침</h2>

<p><strong>{blog_name}</strong>({blog_url})은 방문자의 개인정보 보호를 중요하게 생각합니다. 본 개인정보처리방침은 수집하는 정보의 유형, 사용 목적, 보호 방법을 설명합니다.</p>

<h3>1. 수집하는 정보</h3>
<p>본 블로그는 다음과 같은 정보를 자동으로 수집할 수 있습니다:</p>
<ul>
  <li>IP 주소 및 브라우저 정보</li>
  <li>방문 페이지 및 체류 시간</li>
  <li>참조 사이트 URL</li>
  <li>디바이스 정보 (운영체제, 화면 해상도 등)</li>
</ul>

<h3>2. 쿠키 사용</h3>
<p>본 블로그는 사용자 경험 향상을 위해 쿠키를 사용합니다. 쿠키는 웹사이트가 사용자의 브라우저에 저장하는 작은 텍스트 파일입니다.</p>

<h3>3. 광고</h3>
<p>본 블로그는 Google AdSense를 통해 광고를 게재합니다. Google은 사용자의 관심사에 기반한 광고를 제공하기 위해 쿠키를 사용할 수 있습니다. 사용자는 <a href="https://www.google.com/settings/ads" target="_blank">Google 광고 설정</a>에서 맞춤 광고를 비활성화할 수 있습니다.</p>

<h3>4. 제3자 서비스</h3>
<p>본 블로그는 다음과 같은 제3자 서비스를 사용합니다:</p>
<ul>
  <li>Google Analytics - 웹사이트 트래픽 분석</li>
  <li>Google AdSense - 광고 게재</li>
  <li>Blogger - 블로그 호스팅 플랫폼</li>
</ul>

<h3>5. 연락처</h3>
<p>개인정보 관련 문의사항이 있으시면 블로그 연락처 페이지를 통해 문의해 주세요.</p>

<p><em>최종 업데이트: 2026년 1월</em></p>
"""


def get_about_ko(blog_name: str = "AI 테크 블로그") -> str:
    """블로그 소개 페이지 HTML (한국어)"""
    return f"""
<h2>블로그 소개</h2>

<p><strong>{blog_name}</strong>에 오신 것을 환영합니다!</p>

<h3>🎯 블로그 목적</h3>
<p>이 블로그는 최신 AI 및 기술 뉴스를 한국어와 영어로 전달하는 것을 목표로 합니다. 인공지능, 머신러닝, 빅데이터, 클라우드 컴퓨팅 등 다양한 기술 트렌드를 다룹니다.</p>

<h3>📰 콘텐츠 특징</h3>
<ul>
  <li><strong>다국어 지원</strong>: 모든 글은 한국어와 영어로 제공됩니다</li>
  <li><strong>전문적 분석</strong>: 단순 뉴스 전달을 넘어 기술의 의미와 영향을 분석합니다</li>
  <li><strong>최신 트렌드</strong>: 글로벌 테크 미디어의 최신 소식을 신속하게 전달합니다</li>
</ul>

<h3>📚 주요 카테고리</h3>
<ul>
  <li>AI / 인공지능</li>
  <li>머신러닝 / 딥러닝</li>
  <li>빅테크 기업 뉴스</li>
  <li>스타트업 / 신기술</li>
</ul>

<h3>✉️ 연락처</h3>
<p>협업, 기고, 문의사항이 있으시면 연락처 페이지를 통해 연락해 주세요.</p>

<p>방문해 주셔서 감사합니다!</p>
"""


def get_contact_ko(blog_name: str = "AI 테크 블로그", email: str = "wnwjdwns1@naver.com") -> str:
    """연락처 페이지 HTML (한국어)"""
    return f"""
<h2>연락처</h2>

<p><strong>{blog_name}</strong>에 관심을 가져주셔서 감사합니다.</p>

<h3>📧 이메일</h3>
<p>문의사항이 있으시면 아래 이메일로 연락해 주세요:</p>
<p><strong>{email}</strong></p>

<h3>💬 문의 가능 사항</h3>
<ul>
  <li>블로그 콘텐츠 관련 문의</li>
  <li>광고 및 협업 제안</li>
  <li>기술 기고 요청</li>
  <li>오류 신고 및 피드백</li>
</ul>

<h3>⏰ 응답 시간</h3>
<p>일반적으로 영업일 기준 1-3일 이내에 답변드리겠습니다.</p>
"""


# =============================================================================
# 영어 페이지 (English Pages)
# =============================================================================

def get_privacy_policy_en(blog_name: str = "AI Tech Blog", blog_url: str = "https://besting2.blogspot.com") -> str:
    """Privacy Policy page HTML (English)"""
    return f"""
<h2>Privacy Policy</h2>

<p><strong>{blog_name}</strong> ({blog_url}) takes the privacy of visitors seriously. This Privacy Policy explains the types of information we collect, how we use it, and how we protect it.</p>

<h3>1. Information We Collect</h3>
<p>This blog may automatically collect the following information:</p>
<ul>
  <li>IP address and browser information</li>
  <li>Pages visited and time spent</li>
  <li>Referring site URLs</li>
  <li>Device information (OS, screen resolution, etc.)</li>
</ul>

<h3>2. Use of Cookies</h3>
<p>This blog uses cookies to enhance user experience. Cookies are small text files stored on your browser by websites.</p>

<h3>3. Advertising</h3>
<p>This blog displays advertisements through Google AdSense. Google may use cookies to serve ads based on your interests. You can opt out of personalized advertising at <a href="https://www.google.com/settings/ads" target="_blank">Google Ads Settings</a>.</p>

<h3>4. Third-Party Services</h3>
<p>This blog uses the following third-party services:</p>
<ul>
  <li>Google Analytics - Website traffic analysis</li>
  <li>Google AdSense - Advertisement display</li>
  <li>Blogger - Blog hosting platform</li>
</ul>

<h3>5. Contact</h3>
<p>For privacy-related inquiries, please use the contact page on this blog.</p>

<p><em>Last updated: January 2026</em></p>
"""


def get_about_en(blog_name: str = "AI Tech Blog") -> str:
    """About page HTML (English)"""
    return f"""
<h2>About</h2>

<p>Welcome to <strong>{blog_name}</strong>!</p>

<h3>🎯 Purpose</h3>
<p>This blog aims to deliver the latest AI and technology news in both Korean and English. We cover various tech trends including artificial intelligence, machine learning, big data, and cloud computing.</p>

<h3>📰 Content Features</h3>
<ul>
  <li><strong>Bilingual Support</strong>: All articles are available in Korean and English</li>
  <li><strong>Expert Analysis</strong>: Beyond news delivery, we analyze the meaning and impact of technology</li>
  <li><strong>Latest Trends</strong>: We quickly deliver the latest news from global tech media</li>
</ul>

<h3>📚 Main Categories</h3>
<ul>
  <li>AI / Artificial Intelligence</li>
  <li>Machine Learning / Deep Learning</li>
  <li>Big Tech Company News</li>
  <li>Startups / New Technologies</li>
</ul>

<h3>✉️ Contact</h3>
<p>For collaboration, contributions, or inquiries, please use the contact page.</p>

<p>Thank you for visiting!</p>
"""


def get_contact_en(blog_name: str = "AI Tech Blog", email: str = "wnwjdwns1@naver.com") -> str:
    """Contact page HTML (English)"""
    return f"""
<h2>Contact</h2>

<p>Thank you for your interest in <strong>{blog_name}</strong>.</p>

<h3>📧 Email</h3>
<p>For inquiries, please contact us at:</p>
<p><strong>{email}</strong></p>

<h3>💬 Contact Topics</h3>
<ul>
  <li>Blog content inquiries</li>
  <li>Advertising and collaboration proposals</li>
  <li>Technology contribution requests</li>
  <li>Bug reports and feedback</li>
</ul>

<h3>⏰ Response Time</h3>
<p>We typically respond within 1-3 business days.</p>
"""


# =============================================================================
# 페이지 관리 딕셔너리 (Page Management Dictionary)
# =============================================================================

PAGES_KO: Dict[str, Callable] = {
    "privacy_policy": get_privacy_policy_ko,
    "about": get_about_ko,
    "contact": get_contact_ko,
}

PAGES_EN: Dict[str, Callable] = {
    "privacy_policy": get_privacy_policy_en,
    "about": get_about_en,
    "contact": get_contact_en,
}

PAGES: Dict[str, Dict[str, Callable]] = {
    "ko": PAGES_KO,
    "en": PAGES_EN,
}


def get_page(page_type: str, lang: str = "ko", **kwargs) -> str:
    """
    언어별 페이지 HTML 반환
    
    Args:
        page_type: 페이지 타입 ('privacy_policy', 'about', 'contact')
        lang: 언어 코드 ('ko' 또는 'en')
        **kwargs: 페이지 함수에 전달할 추가 인자
    
    Returns:
        HTML 문자열
    """
    if lang not in PAGES:
        raise ValueError(f"Unsupported language: {lang}. Use 'ko' or 'en'.")
    if page_type not in PAGES[lang]:
        raise ValueError(f"Unknown page type: {page_type}. Use 'privacy_policy', 'about', or 'contact'.")
    
    return PAGES[lang][page_type](**kwargs)


def get_all_pages(lang: str = "ko", **kwargs) -> Dict[str, str]:
    """
    특정 언어의 모든 페이지 HTML 반환
    
    Args:
        lang: 언어 코드 ('ko' 또는 'en')
        **kwargs: 페이지 함수에 전달할 추가 인자
    
    Returns:
        {page_type: html} 딕셔너리
    """
    if lang not in PAGES:
        raise ValueError(f"Unsupported language: {lang}. Use 'ko' or 'en'.")
    
    return {page_type: func(**kwargs) for page_type, func in PAGES[lang].items()}


# =============================================================================
# 레거시 호환 함수 (Legacy Compatibility - 기존 함수 유지)
# =============================================================================

def get_privacy_policy_html(blog_name: str = "AI 테크 블로그", blog_url: str = "https://besting2.blogspot.com") -> str:
    """개인정보처리방침 페이지 HTML 반환 (한국어 + 영어 통합, 레거시 호환)"""
    return get_privacy_policy_ko(blog_name, blog_url) + "\n<hr>\n" + get_privacy_policy_en(blog_name, blog_url)


def get_about_page_html(blog_name: str = "AI 테크 블로그") -> str:
    """블로그 소개 페이지 HTML 반환 (한국어 + 영어 통합, 레거시 호환)"""
    return get_about_ko(blog_name) + "\n<hr>\n" + get_about_en(blog_name)


def get_contact_page_html(blog_name: str = "AI 테크 블로그", email: str = "wnwjdwns1@naver.com") -> str:
    """연락처 페이지 HTML 반환 (한국어 + 영어 통합, 레거시 호환)"""
    return get_contact_ko(blog_name, email) + "\n<hr>\n" + get_contact_en(blog_name, email)


def print_pages_by_lang(lang: str = "ko"):
    """특정 언어의 모든 페이지 HTML 출력"""
    lang_name = "한국어" if lang == "ko" else "English"
    pages = get_all_pages(lang)
    
    page_names = {
        "ko": {"privacy_policy": "개인정보처리방침", "about": "블로그 소개", "contact": "연락처"},
        "en": {"privacy_policy": "Privacy Policy", "about": "About", "contact": "Contact"},
    }
    
    print(f"\n{'=' * 60}")
    print(f"📄 {lang_name} Pages ({lang.upper()})")
    print("=" * 60)
    
    for i, (page_type, html) in enumerate(pages.items(), 1):
        print(f"\n{'-' * 40}")
        print(f"{i}. {page_names[lang][page_type]}")
        print("-" * 40)
        print(html)


def print_all_pages():
    """모든 페이지 HTML 출력 (복사-붙여넣기용) - 언어별 분리"""
    print("=" * 60)
    print("📋 블로그 필수 페이지 HTML 템플릿")
    print("=" * 60)
    
    # 한국어 페이지
    print_pages_by_lang("ko")
    
    # 영어 페이지
    print_pages_by_lang("en")
    
    print("\n" + "=" * 60)
    print("✅ 완료! 위 HTML을 Blogger 페이지에 복사-붙여넣기 하세요.")
    print("=" * 60)


def print_all_pages_combined():
    """모든 페이지 HTML 출력 (한국어+영어 통합 버전, 레거시)"""
    print("=" * 60)
    print("1. 개인정보처리방침 (Privacy Policy)")
    print("=" * 60)
    print(get_privacy_policy_html())
    
    print("\n" + "=" * 60)
    print("2. 블로그 소개 (About)")
    print("=" * 60)
    print(get_about_page_html())
    
    print("\n" + "=" * 60)
    print("3. 연락처 (Contact)")
    print("=" * 60)
    print(get_contact_page_html())


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--combined":
        print_all_pages_combined()
    else:
        print_all_pages()
