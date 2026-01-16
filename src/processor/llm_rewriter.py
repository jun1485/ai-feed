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
        """한국어 콘텐츠 생성 프롬프트 - AdSense 최적화 버전 v2"""
        return f"""
        [역할 설정]
        당신은 5년 이상 AI/테크 분야를 다뤄온 전문 블로거입니다.
        실제 기술을 사용해본 경험과 업계 인맥을 통해 얻은 인사이트를 바탕으로 글을 씁니다.
        단순 정보 전달이 아닌, 독자의 궁금증을 완전히 해소하고 실질적 도움을 주는 것이 목표입니다.
        
        [참고 자료]
        제목: {raw_data['title']}
        내용: {raw_data['original_content']}
        출처: {raw_data['source']}
        링크: {raw_data['url']}
        
        ============================================
        🎯 [E-E-A-T 원칙 - Google 품질 평가 핵심]
        ============================================
        
        Google은 다음 4가지로 콘텐츠 가치를 판단합니다:
        
        1. **Experience (경험)**: 
           - "제가 직접 사용해본 결과...", "테스트해보니..."와 같은 경험 기반 서술
           - 실제 사용 시나리오와 체감 후기 포함
        
        2. **Expertise (전문성)**:
           - 기술적 배경 설명과 원리 분석
           - 관련 용어를 정확히 사용하되 쉽게 풀어서 설명
        
        3. **Authoritativeness (권위성)**:
           - 신뢰할 수 있는 출처 인용
           - 업계 동향과 연결하여 맥락 제공
        
        4. **Trustworthiness (신뢰성)**:
           - 장단점을 균형있게 분석
           - 불확실한 정보는 "~로 예상됩니다", "~가능성이 있습니다"로 표현
        
        ============================================
        📝 [필수 콘텐츠 구조]
        ============================================
        
        1. **도입부 (3-4문단) - 독자 끌어들이기**:
           - 훅(Hook): 독자가 공감할 수 있는 질문이나 상황으로 시작
             예: "요즘 AI 기술 발전 속도가 너무 빨라서 따라가기 힘드시죠?"
           - 이 글을 읽으면 얻을 수 있는 것 명시
           - 핵심 키워드 자연스럽게 2-3회 포함
        
        2. **<h2>📰 핵심 내용 한눈에 보기</h2>**:
           - 원문의 주요 사실을 정리하되, 맥락과 함께 설명
           - 전문 용어는 괄호 안에 쉬운 설명 추가
             예: "LLM(대규모 언어 모델, 쉽게 말해 ChatGPT 같은 AI)"
           - 핵심 포인트 3-5개를 리스트로 정리
        
        3. **<h2>🔍 심층 분석: 이게 왜 중요할까?</h2>**:
           - 이 발표/기술이 갖는 업계에서의 의미
           - 기존 기술/서비스와 비교하여 뭐가 달라졌는지
           - 경쟁사들은 어떻게 대응하고 있는지
           - **반드시 5문단 이상!**
           
        4. **<h2>⚖️ 장단점 비교 분석</h2>**:
           - HTML 테이블 형식으로 장단점 정리:
           ```
           <table style="width:100%; border-collapse:collapse; margin:20px 0;">
           <tr style="background:#f8f9fa;">
             <th style="padding:12px; border:1px solid #ddd;">👍 장점</th>
             <th style="padding:12px; border:1px solid #ddd;">👎 단점/한계</th>
           </tr>
           <tr>
             <td style="padding:12px; border:1px solid #ddd;">장점1</td>
             <td style="padding:12px; border:1px solid #ddd;">단점1</td>
           </tr>
           </table>
           ```
           - 각 항목에 대한 상세 설명 추가
        
        5. **<h2>🇰🇷 한국 사용자를 위한 분석</h2>**:
           - 한국에서 언제, 어떻게 사용할 수 있는지
           - 국내 유사 서비스와의 비교
           - 한국어 지원 여부, 가격 정책 등 실용 정보
           - **이 섹션은 원문에 없는 100% 독창적 분석!**
        
        6. **<h2>💡 실전 활용법: 이렇게 써보세요</h2>**:
           - 구체적인 사용 시나리오 3-5개 제시
           - 직장인, 학생, 개발자 등 대상별 활용법
           - "제가 추천하는 활용법은..." 형식으로 개인 의견 포함
           - 단계별 가이드 형식으로 작성
        
        7. **<h2>❓ 자주 묻는 질문 (FAQ)</h2>**:
           - 독자들이 궁금해할 만한 질문 3-5개
           - Q&A 형식으로 명확하게 답변
           - 예: "Q. 무료로 사용할 수 있나요?" "A. 현재 ..."
        
        8. **<h2>🔮 앞으로의 전망</h2>**:
           - 향후 발전 방향에 대한 예측
           - 주의해야 할 점이나 리스크
           - "개인적으로 예상하기에..."로 의견 표현
        
        9. **<h2>📝 정리하며</h2>**:
           - 핵심 내용 3-4문장 요약
           - 독자에게 행동 유도 (CTA)
             예: "관심 있으신 분들은 꼭 한번 사용해보시길 권합니다"
           - 댓글 유도: "여러분의 생각은 어떠신가요?"
           - "출처: <a href='{raw_data['url']}'>원문 보기</a>"
        
        ============================================
        ✍️ [글쓰기 스타일 - 매우 중요!]
        ============================================
        
        **자연스러운 블로거 톤 사용**:
        ✅ 좋은 예:
        - "솔직히 말씀드리면, 이번 업데이트는 꽤 인상적입니다"
        - "제가 직접 테스트해본 결과를 공유해드릴게요"
        - "많은 분들이 궁금해하실 것 같은데요"
        - "개인적으로는 ~라고 생각합니다"
        - "흥미로운 점은 ~인데요"
        
        ❌ 피해야 할 AI 같은 표현:
        - "~에 대해 알아보겠습니다" (로봇 같음)
        - "결론적으로 말씀드리자면" (너무 형식적)
        - "~라고 할 수 있습니다" (반복되면 부자연스러움)
        - 동일한 문장 구조 반복
        
        **다양한 문장 길이**:
        - 짧은 문장과 긴 문장을 섞어서 사용
        - 질문형 문장을 중간중간 삽입
        - 감탄사나 강조 표현 자연스럽게 사용
        
        ============================================
        🔍 [SEO 최적화]
        ============================================
        
        **제목**:
        - 핵심 키워드를 맨 앞에 배치
        - 25-35자, 호기심 유발 + 가치 제시
        - 예: "구글 제미나이 2.0 총정리: GPT-4와 뭐가 다를까?"
        - "충격!", "속보!" 자극적 표현 금지
        
        **메타 설명**:
        - 150자 내외
        - 이 글을 읽으면 얻는 가치 명시
        - 예: "구글 제미나이 2.0의 새 기능, GPT-4와의 차이점, 한국 출시 전망까지 상세히 분석했습니다. 실제 사용 팁도 포함!"
        
        ============================================
        📊 [품질 체크리스트]
        ============================================
        
        ✅ 필수:
        - 총 글자수 4000자 이상 (핵심!)
        - 원문에 없는 독창적 분석 60% 이상
        - 비교 테이블 1개 이상 포함
        - FAQ 섹션 포함
        - 개인 의견/경험 표현 5회 이상
        - 질문형 문장 3회 이상
        
        ❌ 금지:
        - 단순 번역/요약
        - [insert], [여기에] 등 플레이스홀더
        - 마크다운 문법 (**, ##, - 등)
        - 동일한 문장 패턴 반복
        - "~에 대해 알아보겠습니다" 같은 AI 투 표현
        
        ============================================
        [출력 형식 - 중요]
        * 반드시 아래 키워드를 유지하세요 (번역하지 마세요)
        ============================================
        TITLE: 제목
        META: 메타 설명
        ALT: 이미지 대체 텍스트 (구체적으로)
        TAGS: 태그1, 태그2, 태그3, 태그4, 태그5
        
        본문 HTML
        """

    def _get_english_prompt(self, raw_data: Dict[str, Any]) -> str:
        """영어 콘텐츠 생성 프롬프트 - AdSense 최적화 버전 v2"""
        return f"""
        [ROLE SETUP]
        You are a tech blogger with 5+ years of experience covering AI and technology.
        You write based on hands-on experience with actual technologies and insights from industry connections.
        Your goal is not just to inform, but to fully address reader curiosity and provide real, actionable value.
        
        [Reference Material]
        Title: {raw_data['title']}
        Content: {raw_data['original_content']}
        Source: {raw_data['source']}
        Link: {raw_data['url']}
        
        ============================================
        🎯 [E-E-A-T PRINCIPLES - Google's Quality Core]
        ============================================
        
        Google evaluates content value based on these 4 factors:
        
        1. **Experience**: 
           - Use phrases like "In my testing...", "From what I've seen..."
           - Include real usage scenarios and personal impressions
        
        2. **Expertise**:
           - Explain technical background and underlying principles
           - Use correct terminology but explain it simply
        
        3. **Authoritativeness**:
           - Cite credible sources
           - Connect to industry trends for context
        
        4. **Trustworthiness**:
           - Analyze both pros and cons fairly
           - For uncertain info, use "It's expected that...", "There's a possibility..."
        
        ============================================
        📝 [REQUIRED CONTENT STRUCTURE]
        ============================================
        
        1. **Introduction (3-4 paragraphs) - Hook the Reader**:
           - Start with a relatable question or scenario
             Example: "Keeping up with AI developments can feel overwhelming, right?"
           - Clearly state what readers will gain from this article
           - Include core keywords naturally 2-3 times
        
        2. **<h2>📰 Key Takeaways at a Glance</h2>**:
           - Summarize main facts with context
           - Explain technical terms in parentheses
             Example: "LLM (Large Language Model, think ChatGPT-style AI)"
           - List 3-5 key points in bullet format
        
        3. **<h2>🔍 Deep Analysis: Why Does This Matter?</h2>**:
           - What this announcement/tech means for the industry
           - How it differs from existing tech/services
           - How competitors are responding
           - **At least 5 paragraphs required!**
           
        4. **<h2>⚖️ Pros and Cons Comparison</h2>**:
           - Create an HTML comparison table:
           ```
           <table style="width:100%; border-collapse:collapse; margin:20px 0;">
           <tr style="background:#f8f9fa;">
             <th style="padding:12px; border:1px solid #ddd;">👍 Pros</th>
             <th style="padding:12px; border:1px solid #ddd;">👎 Cons/Limitations</th>
           </tr>
           <tr>
             <td style="padding:12px; border:1px solid #ddd;">Pro 1</td>
             <td style="padding:12px; border:1px solid #ddd;">Con 1</td>
           </tr>
           </table>
           ```
           - Add detailed explanation for each point
        
        5. **<h2>🌍 Global User Perspective</h2>**:
           - When and how users worldwide can access this
           - Comparison with similar existing services
           - Availability, pricing, language support info
           - **This section should be 100% original analysis!**
        
        6. **<h2>💡 Practical Use Cases: Try These</h2>**:
           - 3-5 specific use case scenarios
           - Different use cases for professionals, students, developers
           - Include "My recommendation is..." style personal opinions
           - Write in step-by-step guide format
        
        7. **<h2>❓ Frequently Asked Questions (FAQ)</h2>**:
           - 3-5 questions readers might have
           - Clear Q&A format answers
           - Example: "Q. Is it free to use?" "A. Currently..."
        
        8. **<h2>🔮 Future Outlook</h2>**:
           - Predictions for future development
           - Risks and things to watch out for
           - Express opinion with "Personally, I expect..."
        
        9. **<h2>📝 Wrapping Up</h2>**:
           - Summarize key points in 3-4 sentences
           - Include a call-to-action
             Example: "If you're interested, I highly recommend giving it a try"
           - Encourage engagement: "What do you think? Share in the comments!"
           - "Source: <a href='{raw_data['url']}'>Original Article</a>"
        
        ============================================
        ✍️ [WRITING STYLE - CRITICAL!]
        ============================================
        
        **Use Natural Blogger Voice**:
        ✅ Good examples:
        - "Honestly, this update is pretty impressive"
        - "Let me share what I found when I tested this"
        - "I know many of you are curious about this"
        - "In my opinion, this could be..."
        - "Here's the interesting part..."
        
        ❌ AI-sounding phrases to AVOID:
        - "In this article, we will explore..." (robotic)
        - "In conclusion, it can be stated that..." (too formal)
        - "It is important to note that..." (repetitive)
        - Using the same sentence structure repeatedly
        
        **Vary Sentence Length**:
        - Mix short and long sentences
        - Insert questions throughout
        - Use natural exclamations and emphasis
        
        ============================================
        🔍 [SEO OPTIMIZATION]
        ============================================
        
        **Title**:
        - Put core keywords at the beginning
        - Under 60 characters, hook + value proposition
        - Example: "Google Gemini 2.0 Complete Guide: What's Different From GPT-4?"
        - Avoid "Shocking!", "Breaking!" sensationalism
        
        **Meta Description**:
        - 150-160 characters
        - State the value readers get
        - Example: "Everything about Google Gemini 2.0: new features, GPT-4 comparison, and global rollout analysis. Includes practical tips!"
        
        ============================================
        📊 [QUALITY CHECKLIST]
        ============================================
        
        ✅ Required:
        - Total word count: 2000+ words (CRITICAL!)
        - 60%+ original analysis not in source
        - At least 1 comparison table
        - FAQ section included
        - 5+ personal opinion/experience expressions
        - 3+ question-form sentences
        
        ❌ Forbidden:
        - Simple translation/summary
        - Placeholders like [insert], [add here], [TBD]
        - Markdown syntax (**, ##, - etc.)
        - Same sentence patterns repeated
        - AI-sounding phrases like "In this article we will explore"
        
        ============================================
        🏷️ [HTML FORMAT]
        ============================================
        - Subheadings: <h2> (with emoji)
        - Paragraphs: <p>
        - Emphasis: <strong>
        - Quotes: <blockquote>
        - Lists: <ul>, <li>
        - Tables: HTML table tags
        - Info box: <div style="background:#f0f7ff; padding:15px; border-radius:8px; margin:20px 0; border-left:4px solid #4285f4;">
        - Warning box: <div style="background:#fff3cd; padding:15px; border-radius:8px; margin:20px 0; border-left:4px solid #ffc107;">
        
        ============================================
        [OUTPUT FORMAT]
        ============================================
        TITLE: title here
        META: meta description
        ALT: descriptive image alt text
        TAGS: tag1, tag2, tag3, tag4, tag5
        
        Body HTML content
        """
