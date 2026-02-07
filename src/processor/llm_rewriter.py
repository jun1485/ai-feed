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
<div class="related-posts">
<h3>관련 글 더 보기</h3>
<ul>
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
                model="gemini-2.5-flash",
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
                # 마크다운/특수문자 제거 후 정규화 (파싱 정확도 향상)
                clean_line = line.strip().lstrip("*#-").strip()
                
                if clean_line.upper().startswith("TITLE:") or clean_line.startswith("제목:"):
                    title = clean_line.split(":", 1)[1].strip()
                    content_start_idx = i + 1
                elif clean_line.upper().startswith("META:") or clean_line.startswith("메타:") or clean_line.startswith("메타 설명:"):
                    meta_description = clean_line.split(":", 1)[1].strip()
                    content_start_idx = i + 1
                elif clean_line.upper().startswith("ALT:") or clean_line.startswith("이미지") or clean_line.startswith("ALT 텍스트:"):
                    alt_text = clean_line.split(":", 1)[1].strip()
                    content_start_idx = i + 1
                elif clean_line.upper().startswith("TAGS:") or clean_line.startswith("태그:") or clean_line.startswith("키워드:"):
                    tags_str = clean_line.split(":", 1)[1].strip()
                    tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
                    content_start_idx = i + 1
                elif clean_line and not any(clean_line.upper().startswith(p) for p in ["TITLE:", "META:", "ALT:", "TAGS:", "제목:", "메타:", "태그:", "이미지", "키워드"]):
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
            
            # 한국어 버전 제목 검증: 한글 미포함 시 원본 제목 대신 LLM 재생성 방지용 경고
            if language == "ko" and title == raw_data['title'] and not re.search(r'[가-힣]', title):
                print(f"[경고] 한국어 버전인데 제목이 영어: {title}")
                # LLM이 TITLE을 생성하지 않았으므로 본문 첫 h2 또는 첫 줄에서 추출 시도
                h2_match = re.search(r'<h2[^>]*>(.*?)</h2>', content)
                if h2_match:
                    extracted = re.sub(r'<[^>]+>', '', h2_match.group(1)).strip()
                    if re.search(r'[가-힣]', extracted):
                        title = extracted
                        print(f"[복구] h2에서 한국어 제목 추출: {title}")

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
        """한국어 콘텐츠 생성 프롬프트 - AdSense 승인 최적화 v3"""
        return f"""당신은 AI/테크 전문 칼럼니스트입니다. 아래 참고 자료를 바탕으로,
독자에게 실질적 가치를 제공하는 심층 분석 칼럼을 작성하세요.

[참고 자료]
제목: {raw_data['title']}
내용: {raw_data['original_content']}
출처: {raw_data['source']}
링크: {raw_data['url']}

===== 작성 원칙 =====

1. 독창적 분석 중심:
   - 원문을 단순 번역/요약하지 마세요. 원문은 사실 확인 용도로만 참고하세요.
   - 글의 70% 이상은 원문에 없는 독자적 분석, 맥락, 비교, 전망이어야 합니다.
   - 이 기술/발표가 업계 전체에 미치는 파급효과를 다각도로 분석하세요.
   - 경쟁 제품/서비스와의 구체적 비교를 포함하세요.
   - 한국 시장과 사용자 관점에서의 의미를 반드시 다루세요.

2. 전문가 칼럼 톤:
   - 경험 기반 서술: "실제로 사용해보면...", "업계에서는..."
   - 구체적 수치와 사례를 들어 논점을 뒷받침하세요.
   - 장점뿐 아니라 한계와 우려도 균형있게 다루세요.
   - 불확실한 사항은 "~로 보입니다", "~가능성이 높습니다"로 표현하세요.

3. 자연스러운 글쓰기:
   - 사람이 쓴 칼럼처럼 자연스럽게 작성하세요.
   - 문장 길이와 구조를 다양하게 섞으세요.
   - 중간중간 독자에게 질문을 던지세요.
   - "~에 대해 알아보겠습니다", "결론적으로" 같은 기계적 표현을 쓰지 마세요.
   - 이모지를 사용하지 마세요.

4. 글 구조:
   - 고정된 템플릿을 따르지 마세요. 주제에 맞게 자유롭게 구성하세요.
   - h2 소제목 4-6개를 사용하되, 소제목은 주제에 맞는 구체적 문구를 쓰세요.
   - 예시: "OpenAI와의 격차는 좁혀지고 있는가" (O) / "심층 분석" (X, 너무 포괄적)
   - 글 마지막에 "출처: <a href='{raw_data['url']}'>원문 기사</a>"를 포함하세요.

5. 분량:
   - 최소 5000자 이상 작성하세요.
   - 각 소제목 섹션마다 3문단 이상 작성하세요.

===== HTML 형식 =====
- 소제목: <h2>
- 문단: <p>
- 강조: <strong>
- 목록: <ul>, <ol>, <li>
- 인용: <blockquote>
- 비교표: <table>, <tr>, <th>, <td>
- 인라인 스타일을 사용하지 마세요.

===== 출력 형식 (반드시 준수) =====
- 제목, 메타 설명, 태그, 본문 모두 반드시 한국어로 작성하세요.
- 영어 원문 제목을 그대로 사용하지 마세요. 한국어로 새로 작성하세요.

TITLE: 한국어 SEO 제목 (핵심 키워드 앞 배치, 25-40자, 반드시 한국어)
META: 한국어 메타 설명 (이 글의 핵심 가치 요약, 130-160자)
ALT: 대표 이미지 설명 (구체적, 한국어, 15-25자)
TAGS: 한국어태그1, 한국어태그2, 한국어태그3, 한국어태그4, 한국어태그5

본문 HTML (반드시 한국어)"""

    def _get_english_prompt(self, raw_data: Dict[str, Any]) -> str:
        """영어 콘텐츠 생성 프롬프트 - AdSense 승인 최적화 v3"""
        return f"""You are an AI/tech columnist. Based on the reference material below,
write an in-depth analysis column that provides real value to readers.

[Reference Material]
Title: {raw_data['title']}
Content: {raw_data['original_content']}
Source: {raw_data['source']}
Link: {raw_data['url']}

===== Writing Principles =====

1. Original Analysis First:
   - Do NOT simply summarize or rewrite the source. Use it only for fact-checking.
   - At least 70% of the article must be your own analysis, context, comparisons, and outlook.
   - Analyze the broader industry impact from multiple angles.
   - Include specific comparisons with competing products/services.
   - Discuss implications for different user groups (developers, businesses, consumers).

2. Expert Columnist Tone:
   - Write from experience: "In practice...", "What the industry is seeing..."
   - Support arguments with concrete numbers and examples.
   - Cover both strengths and limitations in a balanced way.
   - For uncertain matters, use "It appears that...", "This likely means..."

3. Natural Writing:
   - Write like a human columnist, not an AI.
   - Vary sentence length and structure.
   - Ask readers questions throughout the piece.
   - NEVER use: "In this article, we will explore...", "In conclusion",
     "It is important to note", "Let's dive in", "Without further ado"
   - Do NOT use emojis.

4. Article Structure:
   - Do NOT follow a rigid template. Structure the article naturally for the topic.
   - Use 4-6 h2 subheadings with specific, descriptive phrases.
   - Good: "Can Google Close the Gap with OpenAI?" / Bad: "Deep Analysis"
   - End with: "Source: <a href='{raw_data['url']}'>Original Article</a>"

5. Length:
   - Minimum 2000 words.
   - Each section under a subheading should have at least 3 paragraphs.

===== HTML Format =====
- Subheadings: <h2>
- Paragraphs: <p>
- Emphasis: <strong>
- Lists: <ul>, <ol>, <li>
- Quotes: <blockquote>
- Comparison tables: <table>, <tr>, <th>, <td>
- Do NOT use inline styles.

===== Output Format =====
TITLE: SEO-optimized title (core keyword first, under 60 chars)
META: Meta description (key value of this article, 130-160 chars)
ALT: Featured image description (specific, 5-10 words)
TAGS: tag1, tag2, tag3, tag4, tag5

Body HTML content"""
