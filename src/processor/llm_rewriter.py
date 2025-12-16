import os
from google import genai
from typing import Dict, Any
from .image_generator import ImageGenerator

class ContentProcessor:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        
        self.image_generator = ImageGenerator()

    def process_content(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.client:
            return {
                "title": f"[Demo] {raw_data['title']}",
                "content": f"Source: {raw_data['url']}\n\n{raw_data['original_content']}",
                "tags": ["AI"],
                "original_url": raw_data['url']
            }

        prompt = f"""
        당신은 조회수 높은 바이럴 콘텐츠 전문 작성자입니다. 
        다음 영어 기술 뉴스를 한국어 블로그 포스팅으로 재작성해주세요.
        
        [원문 정보]
        제목: {raw_data['title']}
        내용: {raw_data['original_content']}
        출처: {raw_data['source']}
        링크: {raw_data['url']}
        
        [조회수 높은 글의 핵심 전략]
        
        1. **제목 (가장 중요! - 센스있게 작성)**:
           [주의] "충격!", "속보!" 같은 뻔한 패턴 반복 금지! 다양한 스타일 활용!
           
           [제목 스타일 - 매번 다른 방식 사용]:
           - 공감형: "결국 일어났다", "우리가 우려했던 일", "예상은 했지만..."
           - 반전형: "근데 진짜 문제는 따로 있다", "...그런데 반전이", "알고 보니"
           - 질문형: "이게 가능하다고?", "왜 아무도 말 안 했을까", "정말 괜찮은 걸까"
           - 비유형: "AI 업계의 지각변동", "판도를 바꿀 한 수", "조용한 혁명"
           - 스토리형: "애플이 결국 손을 들었다", "구글의 조용한 반격이 시작됐다"
           - 인사이트형: "이게 진짜 의미하는 것", "숨겨진 의도가 있다", "겉으로는 안 보이지만"
           - 위트형: "AI도 이건 몰랐을걸", "개발자들 오늘 잠 못 잔다", "커피 한 잔 하고 읽으세요"
           
           [제목 작성 팁]:
           - 핵심 키워드는 앞쪽에 배치
           - 30자 내외로 간결하게
           - 마침표보다 물음표, 말줄임표 활용
           - 독자가 "어? 뭔데?" 하고 클릭하고 싶게
           
           [좋은 예시]:
           - "애플의 AI 전략, 뭔가 이상하다"
           - "GPT-5 루머의 진실...그리고 우리가 놓친 것"
           - "이 기술, 1년 후엔 당연해질 겁니다"
           - "테크 업계가 술렁이는 진짜 이유"
           - "조용히 판을 바꾸고 있는 이 회사"
        
        2. **첫 문장 후킹 (3초 안에 사로잡기)**:
           - 충격적인 사실이나 통계로 시작
           - 또는 "~라면 주목하세요", "~가 바뀌고 있습니다" 형태
           - 독자가 "더 읽고 싶다"고 느끼게 만들기
           - 절대 자기소개나 인사로 시작하지 말 것
        
        3. **감정 유발 글쓰기**:
           - 경외감: "놀라운", "혁신적인", "역대급"
           - 공포/우려: "위험한", "사라질", "대체될"
           - 희망/기대: "드디어", "마침내", "새로운 시대"
           - 분노/논란: "논란", "비판", "문제"
           - 독자가 감정적으로 반응하면 공유 확률 상승
        
        4. **SEO 키워드 전략**:
           - 핵심 키워드를 제목, 첫 문단, 소제목에 자연스럽게 배치
           - 관련 키워드: AI, 인공지능, ChatGPT, 구글, 애플, 삼성, 테크, 기술
           - 롱테일 키워드 활용: "2024년 AI 트렌드", "챗GPT 활용법"
        
        5. **스캔 가능한 구조 (모바일 최적화)**:
           - 한 문단 최대 2-3문장 (짧게!)
           - 소제목(h2, h3)으로 명확한 구조화
           - 핵심은 <strong>태그로 강조 (스캔하는 독자도 핵심 파악)
           - 리스트와 불릿포인트 적극 활용
           - 충분한 여백으로 답답하지 않게
        
        6. **스토리텔링 기법**:
           - 단순 정보 나열이 아닌 이야기 흐름으로 전개
           - "~했는데", "그런데", "결국", "하지만" 등 연결어로 몰입감
           - 구체적 수치, 사례, 비유로 생동감 부여
        
        7. **형식 규칙 (매우 중요!)**:
           - 반드시 HTML 태그만 사용할 것!
           - 마크다운 문법(**, ##, *, - 등) 절대 사용 금지!
           - 소제목: <h2>, <h3>
           - 문단: <p>
           - 강조: <strong> (** 사용 금지)
           - 인용: <blockquote>
           - 리스트: <ul>, <li>
           - 링크: <a href="...">
           - 글 마지막: "출처: <a href='{raw_data['url']}'>원문 보기</a>"
        
        8. **언어 규칙 (절대 준수)**:
           - 반드시 한국어로만 작성
           - 영어는 고유명사(회사명, 제품명, 인명)에만 허용
           - 러시아어, 중국어, 일본어 등 다른 언어 절대 사용 금지
        
        9. **태그/라벨 생성**:
           - 글 내용에 맞는 관련 태그 3-5개 생성
           - 필수 포함: "AI" 또는 "인공지능"
           - 회사명 태그: 구글, 애플, 마이크로소프트, OpenAI, 메타, 삼성, 엔비디아 등
           - 기술 태그: ChatGPT, GPT, LLM, 머신러닝, 딥러닝, 로봇, 자율주행 등
           - 주제 태그: 스타트업, 투자, 빅테크, 반도체, 클라우드, 보안 등
           - 한글 태그 우선, 영어는 고유명사만
        
        [출력 형식]
        첫 줄: "TITLE: 제목"
        둘째 줄: "TAGS: 태그1, 태그2, 태그3, 태그4, 태그5"
        셋째 줄부터: 본문
        """

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[prompt]
            )
            full_text = response.text
            
            # 제목, 태그, 본문 분리
            title = raw_data['title']
            tags = ["AI", "테크뉴스", "인공지능"]  # 기본값
            content = full_text
            
            lines = full_text.split('\n')
            content_start_idx = 0
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith("TITLE:"):
                    title = stripped.replace("TITLE:", "").strip()
                    content_start_idx = i + 1
                elif stripped.startswith("TAGS:"):
                    tags_str = stripped.replace("TAGS:", "").strip()
                    tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
                    content_start_idx = i + 1
                elif stripped and not stripped.startswith("TITLE:") and not stripped.startswith("TAGS:"):
                    # 본문 시작
                    content = "\n".join(lines[i:]).strip()
                    break
            
            # Nano Banana로 이미지 생성 후 상단에 추가
            print("Nano Banana 이미지 생성 중...")
            main_image = self.image_generator.generate_image_html(
                raw_data['title'], 
                alt_text=title
            )
            content = main_image + "\n" + content
            
            return {
                "title": title,
                "content": content,
                "tags": tags,
                "original_url": raw_data['url']
            }
        except Exception as e:
            print(f"Gemini API 오류: {e}")
            return {
                "title": raw_data['title'],
                "content": f"Error: {e}",
                "tags": ["Error"],
                "original_url": raw_data['url']
            }
