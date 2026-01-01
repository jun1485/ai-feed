import os
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

    def process_content(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.client:
            return {
                "title": f"[Demo] {raw_data['title']}",
                "content": f"Source: {raw_data['url']}\n\n{raw_data['original_content']}",
                "tags": ["AI"],
                "meta_description": "",
                "original_url": raw_data['url']
            }

        prompt = f"""
        당신은 SEO 전문가이자 바이럴 콘텐츠 작성자입니다.
        다음 영어 기술 뉴스를 한국어 블로그 포스팅으로 재작성해주세요.
        
        [원문 정보]
        제목: {raw_data['title']}
        내용: {raw_data['original_content']}
        출처: {raw_data['source']}
        링크: {raw_data['url']}
        
        [SEO 최적화 핵심 전략]
        
        1. **제목 작성 (SEO + 클릭 유도 둘 다 필요!)**:
           [필수] 제목에 반드시 핵심 검색 키워드를 포함!
           
           [키워드 우선 제목 패턴]:
           - "[회사명] [제품명] [동작]" + 매력적 후킹
           - 예: "ChatGPT 이미지 생성 기능 출시, 포토샵 대체할까?"
           - 예: "구글 제미나이 2.0 발표, GPT-4 넘어섰나?"
           - 예: "테슬라 로보택시 공개, 2025년 상용화 가능성은?"
           - 예: "애플 AI 시리 업그레이드, 경쟁사 따라잡을 수 있을까?"
           
           [제목 작성 규칙]:
           - 핵심 키워드(회사명, 제품명, 기술명)를 제목 맨 앞에 배치
           - 30자 내외로 간결하게
           - 뒤에 호기심 유발 문구 추가 (?, ... 활용)
           - "충격!", "속보!" 같은 자극적인 표현 금지
           
        2. **메타 설명 (Meta Description) - 매우 중요!**:
           - 150자 내외의 글 요약
           - 핵심 키워드 자연스럽게 포함
           - 클릭 유도하는 문장으로 작성
           - 예: "구글이 발표한 제미나이 2.0의 새로운 기능과 GPT-4와의 비교 분석. AI 업계 판도가 바뀔 수 있는 이유를 알아봅니다."
        
        3. **이미지 설명 (Alt Text)**:
           - 단순히 "이미지"가 아닌 구체적인 설명
           - 예: "ChatGPT 이미지 생성 기능 실제 사용 화면"
           - 예: "구글 제미나이 2.0 발표 현장 사진"
           - 핵심 키워드 포함
        
        4. **본문 SEO 구조**:
           - 첫 문단에 핵심 키워드 자연스럽게 포함
           - <h2> 태그로 소제목 구성 (3-4개)
           - 소제목에도 키워드 포함
           - 본문 1500자 이상 작성
           - 마지막에 요약/결론 섹션 추가
        
        5. **HTML 형식 규칙**:
           - 반드시 HTML 태그만 사용!
           - 마크다운 문법(**, ##, *, - 등) 절대 금지!
           - 소제목: <h2> (절대 h3 이하 사용 금지, 첫 소제목은 h2 필수!)
           - 문단: <p>
           - 강조: <strong>
           - 인용: <blockquote>
           - 리스트: <ul>, <li>
           - 링크: <a href="...">
           - 글 마지막: "출처: <a href='{raw_data['url']}'>원문 보기</a>"
        
        6. **언어 규칙**:
           - 반드시 한국어로만 작성
           - 영어는 고유명사(회사명, 제품명, 인명)에만 허용
        
        7. **태그/라벨 생성**:
           - 글 내용에 맞는 관련 태그 5개 생성
           - 필수: "AI" 또는 관련 기술명
           - 회사명, 제품명, 기술 용어 포함
        
        [출력 형식 - 정확히 지킬 것!]
        첫 줄: "TITLE: 제목"
        둘째 줄: "META: 메타 설명 (150자 내외)"
        셋째 줄: "ALT: 이미지 대체 텍스트"
        넷째 줄: "TAGS: 태그1, 태그2, 태그3, 태그4, 태그5"
        다섯째 줄부터: 본문 (HTML)
        """

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
            
            return {
                "title": title,
                "content": final_content,
                "tags": tags,
                "meta_description": meta_description,
                "original_url": raw_data['url']
            }
            
        except Exception as e:
            print(f"Gemini API 오류: {e}")
            return {
                "title": raw_data['title'],
                "content": f"Error: {e}",
                "tags": ["Error"],
                "meta_description": "",
                "original_url": raw_data['url']
            }
