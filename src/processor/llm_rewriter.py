import os
import google.generativeai as genai
from typing import Dict, Any

class ContentProcessor:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.model = None

    def process_content(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.model:
            return {
                "title": f"[Demo] {raw_data['title']}",
                "content": f"Source: {raw_data['url']}\n\n{raw_data['original_content']}",
                "tags": ["AI"],
                "original_url": raw_data['url']
            }

        prompt = f"""
        당신은 10년 경력의 IT 전문 블로거입니다. 
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
           - 도입부에서 독자의 관심을 확 끌어당기기
           - 핵심 내용을 쉽게 풀어서 설명
           - 업계 전문가처럼 인사이트 제공
           - 마무리에 독자에게 생각할 거리 던지기
        
        3. **형식**: HTML 태그 사용 (h2, h3, p, strong, ul, li)
        
        4. **필수**: 글 마지막에 "출처: [원문 보기]({raw_data['url']})" 포함
        
        [출력 형식]
        첫 줄에 "TITLE: 제목" 형식으로 제목을 쓰고,
        그 다음 줄부터 본문을 작성해주세요.
        """

        try:
            response = self.model.generate_content(prompt)
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
