import os
import re
from google import genai
from typing import Dict, Any, List
from .image_generator import ImageGenerator

# 쿠팡 파트너스 연동 (선택사항)
try:
    from ..affiliate.coupang_partners import CoupangProductRecommender, create_fallback_product_html
    COUPANG_AVAILABLE = True
except ImportError:
    COUPANG_AVAILABLE = False

class ContentProcessor:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        
        self.image_generator = ImageGenerator()
        
        # 쿠팡 파트너스 추천 (API 키가 있으면 활성화)
        self.coupang_recommender = None
        if COUPANG_AVAILABLE:
            self.coupang_recommender = CoupangProductRecommender()
            print("[쿠팡 파트너스] 연동 활성화")
        
        # 최근 발행된 글 목록 (내부 링크용)
        self.recent_posts = []

    def add_recent_post(self, title: str, url: str):
        """최근 발행된 글 추가 (내부 링크용)"""
        self.recent_posts.append({"title": title, "url": url})
        # 최대 10개만 유지
        if len(self.recent_posts) > 10:
            self.recent_posts.pop(0)

    def _generate_internal_links_html(self) -> str:
        """관련 글 내부 링크 HTML 생성"""
        if not self.recent_posts:
            return ""
        
        # 최근 3개 글만 표시
        recent = self.recent_posts[-3:]
        
        links_html = """
<div style="background:#f8f9fa; padding:20px; border-radius:10px; margin:30px 0;">
<h3 style="margin-top:0;">📚 관련 글 더 보기</h3>
<ul style="margin-bottom:0;">
"""
        for post in recent:
            links_html += f'<li><a href="{post["url"]}">{post["title"]}</a></li>\n'
        
        links_html += "</ul></div>"
        return links_html

    def _validate_content(self, content: str) -> str:
        """플레이스홀더 및 저품질 패턴 감지/제거"""
        # AI 플레이스홀더 패턴 감지 (대괄호 안에 지시문이 있는 경우)
        placeholder_patterns = [
            r'\[insert[^\]]*\]',           # [insert ...]
            r'\[add[^\]]*\]',              # [add ...]
            r'\[TBD[^\]]*\]',              # [TBD ...]
            r'\[여기에[^\]]*\]',            # [여기에 ...]
            r'\[추가[^\]]*\]',              # [추가 ...]
            r'\[삽입[^\]]*\]',              # [삽입 ...]
            r'\[필요[^\]]*\]',              # [필요 ...]
            r'\[[^\]]*needed[^\]]*\]',     # [...needed...]
            r'\[[^\]]*required[^\]]*\]',   # [...required...]
            r'\[[^\]]*todo[^\]]*\]',       # [...todo...]
        ]
        
        found_placeholders = []
        for pattern in placeholder_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_placeholders.extend(matches)
        
        if found_placeholders:
            print(f"[경고] 플레이스홀더 발견 및 제거: {found_placeholders}")
            for pattern in placeholder_patterns:
                content = re.sub(pattern, '', content, flags=re.IGNORECASE)
            # 연속된 공백 정리
            content = re.sub(r'\s{2,}', ' ', content)
            content = re.sub(r'\s+([.,;:])', r'\1', content)
        
        return content

    def process_content(self, raw_data: Dict[str, Any], language: str = "ko") -> Dict[str, Any]:
        """
        콘텐츠 처리 및 리라이팅
        
        Args:
            raw_data: 크롤링한 원본 데이터
            language: 'ko' (한국어) 또는 'en' (영어)
        """
        if not self.client:
            return {
                "title": f"[Demo] {raw_data['title']}",
                "content": f"Source: {raw_data['url']}\n\n{raw_data['original_content']}",
                "tags": ["AI"],
                "meta_description": "",
                "original_url": raw_data['url'],
                "language": language
            }

        if language == "en":
            prompt = self._get_english_prompt(raw_data)
        else:
            prompt = self._get_korean_prompt(raw_data)


        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[prompt]
            )
            full_text = response.text
            
            # 파싱: 제목, 메타설명, ALT텍스트, 태그, 본문 분리
            title = raw_data['title']
            meta_description = ""
            alt_text = "AI 관련 뉴스 이미지"
            tags = ["AI", "테크뉴스", "인공지능"]
            content = full_text
            
            lines = full_text.split('\n')
            content_start_idx = 0
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith("TITLE:"):
                    title = stripped.replace("TITLE:", "").strip()
                    content_start_idx = i + 1
                elif stripped.startswith("META:"):
                    meta_description = stripped.replace("META:", "").strip()
                    content_start_idx = i + 1
                elif stripped.startswith("ALT:"):
                    alt_text = stripped.replace("ALT:", "").strip()
                    content_start_idx = i + 1
                elif stripped.startswith("TAGS:"):
                    tags_str = stripped.replace("TAGS:", "").strip()
                    tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
                    content_start_idx = i + 1
                elif stripped and not any(stripped.startswith(p) for p in ["TITLE:", "META:", "ALT:", "TAGS:"]):
                    # 본문 시작
                    content = "\n".join(lines[i:]).strip()
                    # ```html 코드블록 제거
                    if content.startswith("```html"):
                        content = content[7:].strip()  # ```html 제거
                    if content.startswith("```"):
                        content = content[3:].strip()  # ``` 제거
                    if content.endswith("```"):
                        content = content[:-3].strip()  # 마지막 ``` 제거
                    break
            
            # 이미지 생성 (개선된 Alt 텍스트 사용)
            print(f"이미지 생성 중... (Alt: {alt_text})")
            main_image = self.image_generator.generate_image_html(
                raw_data['title'], 
                alt_text=alt_text
            )
            
            # 내부 링크 추가
            internal_links = self._generate_internal_links_html()
            
            # 최종 콘텐츠 조합
            final_content = main_image + "\n" + content
            
            # 내부 링크가 있으면 출처 앞에 삽입
            if internal_links:
                # 출처 링크 찾기
                source_marker = f'출처: <a href="{raw_data["url"]}">'
                if source_marker in final_content:
                    final_content = final_content.replace(
                        source_marker, 
                        internal_links + "\n<p>" + source_marker
                    )
                else:
                    final_content += "\n" + internal_links
            
            # 쿠팡 파트너스 상품 추천 추가
            if self.coupang_recommender:
                try:
                    product_html = self.coupang_recommender.generate_product_html(title, content)
                    if product_html:
                        final_content += "\n" + product_html
                        print("[쿠팡 파트너스] 상품 추천 추가됨")
                except Exception as e:
                    print(f"[쿠팡 파트너스] 상품 추천 실패: {e}")
            
            # 언어별 태그 추가
            lang_tag = "AI-EN" if language == "en" else "AI-KR"
            if lang_tag not in tags:
                tags.append(lang_tag)
            
            # 콘텐츠 검증 (플레이스홀더 제거)
            final_content = self._validate_content(final_content)
            
            return {
                "title": title,
                "content": final_content,
                "tags": tags,
                "meta_description": meta_description,
                "original_url": raw_data['url'],
                "language": language
            }
            
        except Exception as e:
            print(f"Gemini API 오류: {e}")
            return {
                "title": raw_data['title'],
                "content": f"Error: {e}",
                "tags": ["Error"],
                "meta_description": "",
                "original_url": raw_data['url'],
                "language": language
            }

    def _get_korean_prompt(self, raw_data: Dict[str, Any]) -> str:
        """한국어 콘텐츠 생성 프롬프트 - AdSense 최적화 버전"""
        return f"""
        당신은 AI/테크 분야 전문 블로거이자 칼럼니스트입니다.
        다음 기술 뉴스를 바탕으로 **독창적인 분석 기사**를 작성해주세요.
        단순 번역이나 요약이 아닌, 당신만의 관점과 인사이트가 담긴 콘텐츠를 만들어야 합니다.
        
        [참고 자료]
        제목: {raw_data['title']}
        내용: {raw_data['original_content']}
        출처: {raw_data['source']}
        링크: {raw_data['url']}
        
        ============================================
        [핵심 원칙: 독창적 가치 제공]
        ============================================
        
        이 글은 원문 뉴스를 "번역"하는 것이 아닙니다!
        다음을 반드시 포함해야 합니다:
        - 당신만의 해석과 분석
        - 한국 독자에게 유용한 맥락 정보
        - 실용적인 시사점과 활용 방안
        - 관련 배경 지식 설명
        
        ============================================
        [필수 콘텐츠 구조 - 반드시 이 순서로!]
        ============================================
        
        1. **도입부 (2-3문단)**:
           - 왜 이 뉴스가 중요한지 설명
           - 독자가 왜 이 글을 읽어야 하는지 동기 부여
           - 핵심 키워드 자연스럽게 포함
        
        2. **<h2>📰 핵심 내용 정리</h2>**:
           - 원문의 주요 사실을 정리
           - 단순 번역 아님 - 맥락과 함께 설명
           - 전문 용어는 쉽게 풀어서 설명
        
        3. **<h2>🔍 심층 분석: 왜 중요한가?</h2>**:
           - 이 기술/발표가 갖는 의미 분석
           - 업계 트렌드와의 연결성
           - 경쟁사 동향과 비교
           - 최소 4-5문단 이상 작성!
        
        4. **<h2>🇰🇷 한국 시장에 미치는 영향</h2>**:
           - 한국 사용자/기업에게 어떤 의미인지
           - 국내 서비스 출시 가능성
           - 한국 기업들의 대응 전망
           - 이 섹션은 원문에 없는 독창적 분석!
        
        5. **<h2>💡 실용 가이드: 어떻게 활용할까?</h2>**:
           - 일반 사용자가 얻을 수 있는 혜택
           - 개발자/전문가가 주목할 포인트
           - 당장 해볼 수 있는 것들
           - 구체적인 활용 시나리오 제시
        
        6. **<h2>🔮 전망과 예측</h2>**:
           - 향후 발전 방향 예측
           - 주의해야 할 점이나 리스크
           - 장기적 관점에서의 의미
        
        7. **<h2>📝 마치며</h2>**:
           - 핵심 내용 요약 (3-4문장)
           - 독자에게 생각할 거리 제공
           - "출처: <a href='{raw_data['url']}'>원문 보기</a>"
        
        ============================================
        [SEO 최적화]
        ============================================
        
        **제목**:
        - 핵심 키워드(회사명, 제품명)를 맨 앞에 배치
        - 30자 내외, 호기심 유발 문구 추가
        - 예: "구글 제미나이 2.0, GPT-4와 뭐가 다를까? 심층 분석"
        - "충격!", "속보!" 같은 자극적 표현 금지
        
        **메타 설명**:
        - 150자 내외, 핵심 키워드 포함
        - 이 글에서 얻을 수 있는 가치 명시
        
        **이미지 Alt Text**:
        - 구체적인 설명 (예: "구글 제미나이 2.0 기능 비교 인포그래픽")
        
        ============================================
        [품질 기준 - AdSense 승인용]
        ============================================
        
        ✅ 필수 충족사항:
        - 총 글자수 3000자 이상 (매우 중요!)
        - 원문에 없는 독창적 분석 50% 이상
        - 모든 섹션 충실히 작성
        - 한국 독자 맞춤 정보 포함
        - 실용적 가치 제공
        
        ❌ 금지사항:
        - 단순 번역/요약
        - [insert], [여기에] 등 플레이스홀더
        - 마크다운 문법 (**, ##, - 등)
        - 내용 없는 짧은 문단
        - 반복적인 표현
        
        ============================================
        [HTML 형식]
        ============================================
        - 소제목: <h2> (이모지 포함)
        - 문단: <p>
        - 강조: <strong>
        - 인용: <blockquote>
        - 리스트: <ul>, <li>
        - 중요 박스: <div style="background:#f0f7ff; padding:15px; border-radius:8px; margin:20px 0;">
        
        ============================================
        [태그]
        ============================================
        - 5개 생성, "AI" 필수 포함
        - 회사명, 제품명, 기술명 포함
        
        [출력 형식]
        TITLE: 제목
        META: 메타 설명
        ALT: 이미지 대체 텍스트
        TAGS: 태그1, 태그2, 태그3, 태그4, 태그5
        (빈 줄)
        본문 HTML
        """

    def _get_english_prompt(self, raw_data: Dict[str, Any]) -> str:
        """영어 콘텐츠 생성 프롬프트 - AdSense 최적화 버전"""
        return f"""
        You are a professional AI/Tech blogger and columnist.
        Based on the following tech news, write an **original analysis article**.
        This is NOT a rewrite or translation - you must provide YOUR unique perspective and insights.
        
        [Reference Material]
        Title: {raw_data['title']}
        Content: {raw_data['original_content']}
        Source: {raw_data['source']}
        Link: {raw_data['url']}
        
        ============================================
        [CORE PRINCIPLE: Provide Original Value]
        ============================================
        
        This article is NOT about "rewriting" the source news!
        You MUST include:
        - Your own interpretation and analysis
        - Contextual information useful for readers
        - Practical implications and use cases
        - Background knowledge explanation
        
        ============================================
        [REQUIRED CONTENT STRUCTURE - Follow This Order!]
        ============================================
        
        1. **Introduction (2-3 paragraphs)**:
           - Explain why this news matters
           - Motivate readers why they should read this
           - Include core keywords naturally
        
        2. **<h2>📰 Key Takeaways</h2>**:
           - Summarize main facts from the source
           - NOT a simple copy - explain with context
           - Clarify technical terms for general readers
        
        3. **<h2>🔍 Deep Dive: Why This Matters</h2>**:
           - Analyze the significance of this tech/announcement
           - Connect to industry trends
           - Compare with competitor moves
           - Write at least 4-5 paragraphs!
        
        4. **<h2>🌍 Global Market Impact</h2>**:
           - What this means for users and businesses globally
           - Potential rollout timeline in different regions
           - How existing players might respond
           - This section should be YOUR original analysis!
        
        5. **<h2>💡 Practical Guide: How to Use This</h2>**:
           - Benefits for regular users
           - Key points for developers/professionals
           - Things you can try right now
           - Specific use case scenarios
        
        6. **<h2>🔮 Future Outlook</h2>**:
           - Predictions for future development
           - Risks and considerations
           - Long-term implications
        
        7. **<h2>📝 Final Thoughts</h2>**:
           - Summarize key points (3-4 sentences)
           - Give readers something to think about
           - "Source: <a href='{raw_data['url']}'>Original Article</a>"
        
        ============================================
        [SEO OPTIMIZATION]
        ============================================
        
        **Title**:
        - Put core keywords (company, product) at the beginning
        - Under 60 characters, add curiosity-inducing hook
        - Example: "Google Gemini 2.0: How It Differs From GPT-4 - Deep Analysis"
        - Avoid sensational words like "Shocking!", "Breaking!"
        
        **Meta Description**:
        - 150-160 characters, include keywords
        - Clearly state the value readers will get
        
        **Image Alt Text**:
        - Specific description (e.g., "Google Gemini 2.0 feature comparison infographic")
        
        ============================================
        [QUALITY STANDARDS - For AdSense Approval]
        ============================================
        
        ✅ MUST HAVE:
        - Total word count: 1500+ words (VERY IMPORTANT!)
        - 50%+ original analysis not in source
        - All sections thoroughly written
        - Practical value for readers
        - Professional journalism quality
        
        ❌ FORBIDDEN:
        - Simple translation/summary
        - Placeholders like [insert], [add here], [TBD]
        - Markdown syntax (**, ##, - etc.)
        - Short, empty paragraphs
        - Repetitive expressions
        
        ============================================
        [HTML FORMAT]
        ============================================
        - Subheadings: <h2> (with emoji)
        - Paragraphs: <p>
        - Emphasis: <strong>
        - Quotes: <blockquote>
        - Lists: <ul>, <li>
        - Highlight box: <div style="background:#f0f7ff; padding:15px; border-radius:8px; margin:20px 0;">
        
        ============================================
        [TAGS]
        ============================================
        - Generate 5 tags, "AI" is required
        - Include company names, product names, tech terms
        
        [OUTPUT FORMAT]
        TITLE: title here
        META: meta description
        ALT: image alt text
        TAGS: tag1, tag2, tag3, tag4, tag5
        (blank line)
        Body HTML content
        """
