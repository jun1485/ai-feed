import os
import re
import random
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
        """플레이스홀더, AI 생성 패턴, 저품질 신호 감지/제거"""
        # 프롬프트 라벨 텍스트 제거 (LLM이 출력 형식 안내문을 본문에 포함하는 경우)
        label_patterns = [
            r'본문\s*HTML[^\n<]*',
            r'Body\s*HTML[^\n<]*',
            r'<p>\s*본문\s*:?\s*</p>',
            r'<p>\s*Body\s*:?\s*</p>',
        ]
        for pattern in label_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                print(f"[경고] 프롬프트 라벨 텍스트 발견 및 제거: {pattern}")
                content = re.sub(pattern, '', content, flags=re.IGNORECASE)

        # AI 플레이스홀더 패턴 감지 (대괄호 안에 지시문이 있는 경우)
        placeholder_patterns = [
            r'\[insert[^\]]*\]',
            r'\[add[^\]]*\]',
            r'\[TBD[^\]]*\]',
            r'\[여기에[^\]]*\]',
            r'\[추가[^\]]*\]',
            r'\[삽입[^\]]*\]',
            r'\[필요[^\]]*\]',
            r'\[[^\]]*needed[^\]]*\]',
            r'\[[^\]]*required[^\]]*\]',
            r'\[[^\]]*todo[^\]]*\]',
            r'\[예시[^\]]*\]',
            r'\[참고[^\]]*\]',
        ]

        found_placeholders = []
        for pattern in placeholder_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_placeholders.extend(matches)

        if found_placeholders:
            print(f"[경고] 플레이스홀더 발견 및 제거: {found_placeholders}")
            for pattern in placeholder_patterns:
                content = re.sub(pattern, '', content, flags=re.IGNORECASE)

        # AI 생성 문구 패턴 제거
        ai_phrases = [
            r'에 대해 알아보겠습니다',
            r'함께 살펴보겠습니다',
            r'해 보도록 하겠습니다',
            r'라고 할 수 있습니다',
            r'결론적으로',
            r'마무리하며',
            r'주목할 만하다',
            r'눈여겨볼 만하다',
            r'귀추가 주목된다',
            r'In this article',
            r'Let\'s dive in',
            r'Without further ado',
            r'It remains to be seen',
            r'Only time will tell',
        ]
        for phrase in ai_phrases:
            if re.search(phrase, content, re.IGNORECASE):
                print(f"[경고] AI 생성 문구 발견: {phrase}")

        # 빈 HTML 태그 제거 (내용 없는 <p></p>, <h2></h2> 등)
        content = re.sub(r'<(p|h2|h3|li|blockquote)>\s*</(p|h2|h3|li|blockquote)>', '', content)

        # 연속된 공백/빈 줄 정리
        content = re.sub(r'\n{3,}', '\n\n', content)
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
        """한국어 콘텐츠 생성 프롬프트 - 독창적 분석 + AdSense 정책 준수 v5"""
        # 매 글마다 다른 도입 각도/분석 프레임으로 패턴 방지
        angles = [
            "이 기술의 역사적 맥락에서 왜 지금 이 시점이 중요한지",
            "경쟁사들의 대응과 업계 전체 판도 변화 분석",
            "실제 현업 개발자/사용자 입장에서의 체감 영향",
            "비즈니스 모델 관점에서 이 결정의 의미",
            "기술 성숙도 곡선에서 현재 위치와 향후 궤적",
            "한국 IT 생태계에 미칠 구체적 파급 효과",
        ]
        analysis_frameworks = [
            "기술적 원리를 분해해서 왜 이게 기존과 다른지 설명",
            "3년 후 이 기술이 만들어낼 구체적 시나리오 제시",
            "유사한 과거 사례와 비교해서 패턴 분석",
            "찬반 양측의 핵심 논점을 정리하고 본인 입장 표명",
            "이 변화가 일반 소비자에게 의미하는 바를 구체적 예시로 설명",
        ]
        personal_experiences = [
            "관련 기술을 직접 사용해본 경험을 바탕으로",
            "최근 프로젝트에서 비슷한 문제를 겪은 경험을 녹여서",
            "동료 개발자들과 이 주제로 토론한 내용을 반영해서",
            "이 분야 컨퍼런스에서 들은 인사이트를 결합해서",
            "실무에서 이 기술의 한계를 체감한 경험을 담아서",
        ]
        angle = random.choice(angles)
        framework = random.choice(analysis_frameworks)
        experience = random.choice(personal_experiences)
        section_count = random.randint(4, 6)

        return f"""아래 기사의 주제를 활용해서, 완전히 독창적인 심층 분석 블로그 글을 작성해줘.

[핵심 원칙 - 반드시 지켜야 함]
이 글은 원문 기사의 '번역'이나 '재작성'이 아니다.
원문은 주제의 출발점일 뿐이다. 원문에 없는 네 고유의 분석, 맥락, 통찰, 예측이 글의 80% 이상을 차지해야 한다.
독자가 원문을 이미 읽었더라도, 이 글에서만 얻을 수 있는 새로운 가치가 있어야 한다.

[너는 누구인가]
IT 업계 10년차 이상 경력의 테크 블로거이자 현직 개발자.
기술을 직접 구현하고 운영해본 실무 경험이 풍부하다.
새로운 기술 발표를 보면, 마케팅 메시지 뒤에 숨은 기술적 실체를 파악하고
그것이 실제 산업과 개인에게 어떤 영향을 미칠지 분석하는 것이 전문이다.
블로그는 편하게 쓴다. 친구한테 카톡으로 설명해주듯이, 전문 용어는 쉽게 풀어서.
독자는 IT에 관심 있는 일반인부터 업계 종사자까지 다양하다.

[참고 기사 - 주제의 출발점으로만 활용]
제목: {raw_data['title']}
내용: {raw_data['original_content']}
출처: {raw_data['source']}
링크: {raw_data['url']}

[독창적 가치 추가 요구사항 - 가장 중요]

1. 분석 각도: "{angle}" 관점에서 깊이 있게 분석해.
2. 분석 방법: "{framework}"
3. 경험 반영: "{experience}" 글에 녹여.
4. 원문에 없는 독자적 콘텐츠를 반드시 포함:
   - 관련 기술의 역사적 발전 과정이나 배경 지식
   - 경쟁사/대안 기술과의 구체적 비교 분석
   - 실제 사용 사례나 구현 경험담 (구체적 도구명, 버전, 설정 등)
   - 데이터나 수치를 활용한 시장/기술 분석
   - 한국 IT 시장에서의 구체적 적용 가능성과 현실적 제약
   - 앞으로 6개월~2년 내 예상되는 변화에 대한 구체적 예측
5. 원문 기사의 내용을 그대로 옮기는 문단이 하나라도 있으면 실패.
   원문의 사실 정보는 네 분석의 근거로만 활용하고, 서술은 완전히 새로 작성.

[글쓰기 규칙]

1. 도입부: 독자의 관심을 끄는 구체적 에피소드, 통계, 또는 질문으로 시작.
   뻔한 "오늘 이런 소식이 있었어요" 패턴 금지.
   예시: 실제 수치로 시작하거나, 독자가 겪었을 법한 상황을 묘사하거나,
   논쟁적인 주장으로 시작하는 등 매번 다른 방식으로.

2. 소제목은 {section_count}개. 소제목은 그 섹션의 핵심 논점을 담은 구체적 문장으로.
   나쁜 예: "핵심 분석", "앞으로의 전망", "기술적 특징"
   좋은 예: "왜 지금 1000억 달러를 쏟아붓는 걸까?", "이게 우리 일상에 미칠 변화",
   "구글이 이 전략을 선택한 진짜 이유"

3. 톤은 친구한테 설명해주는 느낌이되, 반드시 존댓말(해요체)로 통일:
   - 문장 끝은 반드시 "~요", "~죠", "~거든요", "~더라고요", "~잖아요" 등 해요체로 끝내.
   - 반말 종결("~거다", "~말이다", "~아니다", "~했다", "~인 거다", "~보자") 절대 금지.
   - "~것이다", "~된다", "~있다" 같은 딱딱한 문어체 종결도 금지.
   - 짧은 문장, 긴 문장 섞어. 가끔 한 줄짜리 문단도 OK.
   - 같은 단어를 한 문단 안에서 반복하지 마.
   - 이런 표현 절대 쓰지 마: "~에 대해 알아보겠습니다", "~라고 할 수 있습니다",
     "결론적으로", "주목할 만하다", "눈여겨볼 만하다", "귀추가 주목된다",
     "함께 살펴보겠습니다", "~해 보도록 하겠습니다", "마무리하며"
   - 이모지 사용 금지.

4. 가독성 (매우 중요):
   - <p> 하나에 최대 2~3문장. 4문장 이상 절대 금지.
   - 핵심 주장이나 감탄은 한 문장만 단독 <p>로 빼.
   - 긴 설명이 이어질 때는 <ul>/<ol> 리스트로 끊어줘.
   - 인용이나 핵심 수치는 <blockquote>로 강조.
   - 소제목(<h2>) 바로 아래 첫 <p>는 2문장 이내로 짧게 시작.
   - 한 섹션 안에서 <p>만 5개 이상 연속되면 중간에 <blockquote>, <ul>, <strong> 등으로 시각적 변화를 줘.
   - 숫자/비교 데이터가 3개 이상이면 반드시 <table>이나 <ul>로 정리.

5. 독자적 분석 필수 요소 (각 소제목 섹션마다 최소 1개):
   - 본인만의 해석이나 의견 ("제가 보기엔", "솔직히 이건", "경험상")
   - 구체적 근거나 사례 (수치, 비교, 실제 사용 경험)
   - 원문에 없는 추가 맥락이나 배경 정보
   - 실무적 시사점이나 actionable insight

6. 한국 상황은 글 흐름 속에 자연스럽게 녹여:
   - 별도 섹션 만들지 마. "국내에서는", "우리나라에서는" 같은 식으로.
   - 한국 기업, 서비스, 규제 환경 등 구체적으로 언급.

7. 마무리는 가볍지만 생각할 거리를 남겨:
   - "여러분은 어떻게 생각하세요?" 같은 뻔한 마무리 금지.
   - 구체적 예측, 실무적 제안, 또는 독자에게 실질적 도움이 되는 팁으로 끝내.
   - 출처 넣어: 출처: <a href="{raw_data['url']}">원문 기사</a>

8. 분량: 7000자 이상. 각 소제목 아래 4문단 이상.
   원문 기사보다 훨씬 풍부한 분량과 깊이를 가져야 함.

[HTML 형식]
<h2>, <p>, <strong>, <ul>, <ol>, <li>, <blockquote>, <table> 사용.
인라인 스타일 금지. 마크다운 문법 금지.

구조 예시 (이 패턴을 따라):
<p>짧은 도입 1~2문장.</p>
<p>부연 설명 2~3문장.</p>
<p>한 줄 강조 문장.</p>
<blockquote>핵심 수치나 인용</blockquote>
<ul>
<li>비교 항목 1</li>
<li>비교 항목 2</li>
</ul>
<p>분석 2~3문장.</p>

[출력 형식]
TITLE: 한국어 제목 (영어 원문 그대로 쓰지 마. 한국어로 새로 작성. SEO 최적화)
META: 한국어 메타 설명 (130-160자, 독자가 클릭하고 싶게)
ALT: 이미지 설명 (한국어, 15-25자)
TAGS: 태그1, 태그2, 태그3, 태그4, 태그5

이 4줄 다음 빈 줄 후 바로 <p>로 본문 시작. 라벨 텍스트 출력 금지."""

    def _get_english_prompt(self, raw_data: Dict[str, Any]) -> str:
        """영어 콘텐츠 생성 프롬프트 - 독창적 분석 + AdSense 정책 준수 v5"""
        personas = [
            "A former software engineer turned tech blogger with 12 years of hands-on experience. You've shipped production systems and know the gap between demos and reality.",
            "An ex-startup founder who now writes about tech. You see technology through a business model and market viability lens.",
            "A tech journalist with 10 years of experience. You dig into the context, follow the money, and connect dots others miss.",
            "A CS professor who started blogging to make tech accessible. You explain the fundamental principles behind the hype.",
            "A product manager turned tech writer. You think about user impact, adoption curves, and what actually ships vs. what gets announced.",
        ]
        analysis_angles = [
            "Focus on the historical context and why this timing matters in the industry's evolution.",
            "Analyze the competitive landscape and how this shifts the power dynamics among key players.",
            "Examine the practical, real-world implications for developers and end users.",
            "Evaluate the business model implications and long-term sustainability.",
            "Compare with similar past developments to identify patterns and predict outcomes.",
            "Assess the technical architecture decisions and their trade-offs.",
        ]
        persona = random.choice(personas)
        angle = random.choice(analysis_angles)
        section_count = random.randint(4, 6)

        return f"""Write an original, in-depth analysis blog post using the article below as a starting point.

[CORE PRINCIPLE - MUST FOLLOW]
This post is NOT a rewrite or summary of the source article.
The source is merely a jumping-off point. Your own unique analysis, context, insights,
and predictions must make up 80%+ of the content.
A reader who already read the source must find NEW value in your post that exists nowhere else.

[Your Profile]
{persona}
Your readers are tech-curious professionals, not necessarily engineers.

[Source Article - Use as starting point only]
Title: {raw_data['title']}
Content: {raw_data['original_content']}
Source: {raw_data['source']}
Link: {raw_data['url']}

[Original Value Requirements - MOST IMPORTANT]

1. Analysis angle: {angle}
2. You MUST include content NOT found in the source:
   - Historical context and background of the technology/company
   - Concrete comparisons with competitors or alternative approaches
   - Real-world implementation experiences (specific tools, versions, configurations)
   - Data-driven market or technology analysis
   - Specific predictions for the next 6-24 months with reasoning
   - Practical takeaways readers can act on
3. If any paragraph simply restates what the source says, the post fails.
   Use source facts only as evidence for YOUR analysis. All narrative must be original.

[Writing Rules]

1. Opening: Start with a specific anecdote, striking statistic, or provocative claim.
   Do NOT use generic openings like "Today I want to talk about..."
   Each post should open differently - a number, a scenario, a contrarian take.

2. Use exactly {section_count} subheadings. Each must be a specific argument or question.
   Bad: "Key Analysis", "Future Outlook", "Technical Details"
   Good: "Why Nvidia Is Betting $100B Right Now", "The Real Threat to OpenAI's Moat",
   "What Every Developer Should Do Before Q3"

3. Writing style (CRITICAL):
   - Mix short sentences with longer ones. Create rhythm.
   - Use one-sentence paragraphs occasionally. "That's a big deal."
   - Never have 3+ sentences in a row ending with the same structure.
   - Don't repeat the same word within a paragraph.
   - BANNED phrases: "In this article", "It is important to note",
     "Let's dive in", "Without further ado", "In conclusion",
     "It remains to be seen", "Only time will tell", "game-changer",
     "Let's explore", "Let's take a closer look", "In summary"
   - No emojis.

4. Readability (VERY IMPORTANT):
   - Max 2-3 sentences per <p>. Never 4+ sentences in one <p>.
   - Pull out key claims as standalone single-sentence <p> tags.
   - When listing 3+ items, use <ul>/<ol> instead of prose.
   - Use <blockquote> for key stats, quotes, or standout numbers.
   - First <p> after each <h2> should be short (1-2 sentences).
   - If 5+ <p> tags appear in a row, break with <blockquote>, <ul>, or <strong>.
   - Use <table> for any comparison of 3+ data points.

5. Original analysis required in EVERY section:
   - Your own interpretation ("In my experience", "Having built similar systems")
   - Concrete evidence (numbers, comparisons, real use cases)
   - Context not found in the source article
   - Actionable insights or practical implications

6. Take a clear stance. Don't hedge everything.
   Say things like: "Honestly, this is underwhelming", "I think they're onto something",
   "This feels overhyped and here's why."

7. End with a concrete prediction or practical recommendation. Not "What do you think?"
   Something specific and actionable.
   Then add: Source: <a href="{raw_data['url']}">Original Article</a>

8. Length: 3000+ words. At least 4 paragraphs per section.
   Your post must be significantly richer and deeper than the source article.

[HTML Format]
<h2>, <p>, <strong>, <ul>, <ol>, <li>, <blockquote>, <table>.
No inline styles. No markdown.

Structure example (follow this pattern):
<p>Short intro, 1-2 sentences.</p>
<p>Elaboration, 2-3 sentences.</p>
<p>One-line emphasis.</p>
<blockquote>Key stat or quote</blockquote>
<ul>
<li>Comparison item 1</li>
<li>Comparison item 2</li>
</ul>
<p>Analysis, 2-3 sentences.</p>

[Output Format]
TITLE: SEO title (under 60 chars)
META: Meta description (130-160 chars)
ALT: Image description (5-10 words)
TAGS: tag1, tag2, tag3, tag4, tag5

After these 4 lines and a blank line, start body with <p>. No labels."""
