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
        당신은 AI-feed 블로그 작성 봇입니다. 게시글에 인사와 소개를 적지 마세요.
        다음 영어 기술 뉴스를 한국어 블로그 포스팅으로 재작성해주세요.
        
        [원문 정보]
        제목: {raw_data['title']}
        내용: {raw_data['original_content']}
        출처: {raw_data['source']}
        링크: {raw_data['url']}
        
        [작성 규칙]
        1. **제목**: 클릭을 유도하는 자극적이고 궁금증을 자아내는 한국어 제목
           - 예시: "충격! 구글이 숨기고 있던 AI의 진실", "이거 모르면 손해! AI 업계 초특급 뉴스"
           - 숫자, 감탄사, 질문형 활용
        
        2. **본문**: 
           - 전문적이고 권위 있는 어조 (합니다/입니다 체)
           - 바로 핵심 내용부터 시작 (자기소개 하지 말 것)
           - 원문 내용을 상세하게 풀어서 설명
           - 관련 배경 지식이나 맥락도 추가 설명
           - 독자가 이해하기 쉽게 예시나 비유 활용
           - 마무리는 간단하게 요약만 (댓글 요청, 구독 요청 등 하지 말 것)
        
        3. **형식**: HTML 태그 사용 (h2, h3, p, strong, ul, li)
           - 소제목(h2, h3)을 2-3개 사용하여 구조화
           - 중요 포인트는 불릿 리스트로 정리
        
        4. **필수**: 글 마지막에 "출처: <a href='{raw_data['url']}'>원문 보기</a>" 포함
        
        [출력 형식]
        첫 줄에 "TITLE: 제목" 형식으로 제목을 쓰고,
        그 다음 줄부터 본문을 작성해주세요.
        """

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[prompt]
            )
            full_text = response.text
            
            # 제목과 본문 분리
            title = raw_data['title']
            content = full_text
            
            lines = full_text.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith("TITLE:"):
                    title = line.replace("TITLE:", "").strip()
                    content = "\n".join(lines[i+1:]).strip()
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
                "tags": ["AI", "테크뉴스", "인공지능"],
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
