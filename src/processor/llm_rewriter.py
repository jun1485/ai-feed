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
        """플레이스홀더 및 저품질 패턴 감지/제거"""
        # 프롬프트 라벨 텍스트 제거 (LLM이 출력 형식 안내문을 본문에 포함하는 경우)
        label_patterns = [
            r'본문\s*HTML[^\n<]*',
            r'Body\s*HTML[^\n<]*',
        ]
        for pattern in label_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                print(f"[경고] 프롬프트 라벨 텍스트 발견 및 제거: {pattern}")
                content = re.sub(pattern, '', content, flags=re.IGNORECASE)

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
        """한국어 콘텐츠 생성 프롬프트 - 사람 글쓰기 스타일 v4"""
        # 매 글마다 다른 오프닝/전환으로 패턴 깨기
        openers = [
            "오늘 이 소식 보고 좀 흥분했다. 개발자로서 이건 그냥 넘길 수가 없었다.",
            "출근길에 이 기사 보고 회사 도착하자마자 동료한테 슬랙 보냈다.",
            "솔직히 처음엔 '또 이런 뉴스야?' 했는데, 읽다 보니 생각이 완전 바뀌었다.",
            "어제 야근하면서 이 소식 접했는데, 피곤한 것도 잊고 한참 읽었다.",
            "개발자 커뮤니티에서 이 얘기가 엄청 돌고 있길래 원문을 찾아봤다.",
            "이번 주에 본 테크 뉴스 중에 이게 단연 가장 흥미로웠다.",
        ]
        transitions = [
            "근데 여기서 개발자로서 한 가지 짚고 넘어갈 게 있다.",
            "사실 더 중요한 건 따로 있다고 본다.",
            "근데 이걸 실제로 쓰는 입장에서 생각해보면 얘기가 좀 달라진다.",
            "여기서 좀 다른 각도로 생각해보자.",
            "잠깐, 이 부분은 현업 개발자 입장에서 좀 더 파볼 필요가 있다.",
        ]
        opener = random.choice(openers)
        transition = random.choice(transitions)
        section_count = random.randint(3, 5)

        return f"""아래 기사를 참고해서, 네 블로그에 올릴 글을 써줘.

[너는 누구인가]
현직 프론트엔드 개발자. React, Vue 등을 매일 다루고, 새로운 기술이 나오면 직접 써보는 걸 좋아한다.
블로그는 편하게 쓴다. 친구한테 카톡으로 설명해주듯이, 쉽고 재밌게.
독자는 개발 입문자부터 주니어 개발자, IT에 관심 있는 일반인까지 다양하다.

[참고 기사]
제목: {raw_data['title']}
내용: {raw_data['original_content']}
출처: {raw_data['source']}
링크: {raw_data['url']}

[글쓰기 규칙]

1. 첫 문단은 이렇게 시작해: "{opener}" 이 문장으로 시작하되, 자연스럽게 이어서 써.

2. 원문을 번역하거나 요약하지 마. 참고만 하고, 네 관점으로 완전히 새로운 글을 써.
   원문에 나온 사실은 활용하되, 분석/의견/맥락은 전부 네가 만들어.

3. 글 중간에 이 전환 문장을 한 번 써: "{transition}"

4. 소제목은 {section_count}개만 써. 소제목은 그 섹션의 핵심 논점을 담은 구체적 문장으로.
   나쁜 예: "핵심 분석", "앞으로의 전망"
   좋은 예: "엔비디아가 이 시점에 1000억 달러를 베팅하는 이유", "한국 AI 스타트업에 미칠 영향"

5. 톤은 친구한테 설명해주는 느낌으로:
   - "~하거든요", "~더라고요", "~인 거죠", "~잖아요" 같은 구어체를 자연스럽게 써.
   - 짧은 문장, 긴 문장 섞어. 가끔 한 줄짜리 문단도 OK. "이건 진짜 대박이다."
   - "~것이다", "~된다", "~있다"로 끝나는 문장이 3번 연속 오면 안 됨.
   - 같은 단어를 한 문단 안에서 반복하지 마.
   - 이런 표현 절대 쓰지 마: "~에 대해 알아보겠습니다", "~라고 할 수 있습니다",
     "결론적으로", "주목할 만하다", "눈여겨볼 만하다", "귀추가 주목된다"
   - 이모지 사용 금지.

6. 가독성 (매우 중요):
   - <p> 하나에 최대 2~3문장. 4문장 이상 절대 금지.
   - 핵심 주장이나 감탄은 한 문장만 단독 <p>로 빼: <p>이건 진짜 게임 체인저다.</p>
   - 긴 설명이 이어질 때는 <ul>/<ol> 리스트로 끊어줘.
   - 인용이나 핵심 수치는 <blockquote>로 강조.
   - 소제목(<h2>) 바로 아래 첫 <p>는 2문장 이내로 짧게 시작.
   - 한 섹션 안에서 <p>만 5개 이상 연속되면 중간에 <blockquote>, <ul>, <strong> 등으로 시각적 변화를 줘.
   - 숫자/비교 데이터가 3개 이상이면 반드시 <table>이나 <ul>로 정리.

7. 개발자답게 솔직한 의견:
   - "이거 써보니까 진짜 편하더라", "근데 이건 좀 아쉽다", "과대평가된 감이 있다"
   - 기술의 장단점에 대해 확실한 입장을 취해. 양비론 금지.
   - 가능하면 개발 경험과 연결해서 써. "프로젝트에서 이런 걸 쓴다면..."

8. 한국 상황은 글 흐름 속에 자연스럽게:
   - 별도 섹션 만들지 마. "국내에서는", "우리나라 개발자들 사이에서는" 같은 식으로 녹여.

9. 마무리는 가볍지만 생각할 거리를 남겨:
   - "여러분은 어떻게 생각하세요?" 같은 뻔한 마무리 대신,
     하나의 예측이나 개발자로서의 다짐 같은 걸로 끝내.
   - 출처 넣어: 출처: <a href="{raw_data['url']}">원문 기사</a>

10. 분량: 5000자 이상. 각 소제목 아래 3문단 이상.

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
TITLE: 한국어 제목 (영어 원문 그대로 쓰지 마. 한국어로 새로 작성)
META: 한국어 메타 설명 (130-160자)
ALT: 이미지 설명 (한국어, 15-25자)
TAGS: 태그1, 태그2, 태그3, 태그4, 태그5

이 4줄 다음 빈 줄 후 바로 <p>로 본문 시작. 라벨 텍스트 출력 금지."""

    def _get_english_prompt(self, raw_data: Dict[str, Any]) -> str:
        """영어 콘텐츠 생성 프롬프트 - 사람 글쓰기 스타일 v4"""
        personas = [
            "A former software engineer turned tech blogger. You know the real challenges of building things.",
            "An ex-startup founder who now writes about tech. You see technology through a business lens.",
            "A tech journalist with 10 years of experience. You dig into the context behind every headline.",
            "A CS professor who started blogging to make tech accessible. You explain the why, not just the what.",
            "A product manager turned tech writer. You think about how technology actually ships and scales.",
        ]
        openers = [
            "I've been chewing on this one for a while now.",
            "When this news dropped, my first thought was: finally.",
            "I almost scrolled past this story. Glad I didn't.",
            "A friend in the industry pinged me about this, and honestly, I was skeptical at first.",
            "This one caught me off guard. And I don't say that often.",
            "I read this piece over my morning coffee and had to set the cup down halfway through.",
        ]
        persona = random.choice(personas)
        opener = random.choice(openers)
        section_count = random.randint(3, 5)

        return f"""Write a blog post based on the article below.

[Your Profile]
{persona}
Your readers are tech-curious professionals, not necessarily engineers.

[Source Article]
Title: {raw_data['title']}
Content: {raw_data['original_content']}
Source: {raw_data['source']}
Link: {raw_data['url']}

[Writing Rules]

1. Start your first paragraph with: "{opener}" Then continue naturally.

2. Do NOT summarize or rewrite the source. Use it as a factual reference only.
   All analysis, opinions, and context must be your own.

3. Use exactly {section_count} subheadings. Each must be a specific argument or question.
   Bad: "Key Analysis", "Future Outlook"
   Good: "Why Nvidia Is Betting $100B Right Now", "The Real Threat to OpenAI's Moat"

4. Writing style rules (CRITICAL):
   - Mix short sentences with longer ones. Create rhythm.
   - Use one-sentence paragraphs occasionally. "That's a big deal."
   - Never have 3+ sentences in a row ending with the same structure.
   - Don't repeat the same word within a paragraph.
   - BANNED phrases: "In this article", "It is important to note",
     "Let's dive in", "Without further ado", "In conclusion",
     "It remains to be seen", "Only time will tell", "game-changer"
   - No emojis.

5. Readability (VERY IMPORTANT):
   - Max 2-3 sentences per <p>. Never 4+ sentences in one <p>.
   - Pull out key claims or reactions as standalone single-sentence <p> tags.
   - When listing 3+ items, use <ul>/<ol> instead of prose.
   - Use <blockquote> for key stats, quotes, or standout numbers.
   - First <p> after each <h2> should be short (1-2 sentences).
   - If 5+ <p> tags appear in a row, break the pattern with <blockquote>, <ul>, or <strong>.
   - Use <table> for any comparison of 3+ data points.

6. Take a clear stance. Don't hedge everything.
   Say things like: "Honestly, this is underwhelming", "I think they're onto something",
   "This feels overhyped."

7. End with a thought-provoking prediction or question. Not "What do you think?"
   Something specific. Then add: Source: <a href="{raw_data['url']}">Original Article</a>

8. Length: 2000+ words. At least 3 paragraphs per section.

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
