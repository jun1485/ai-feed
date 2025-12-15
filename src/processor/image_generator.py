import os
import base64
from typing import Optional
from google import genai

class ImageGenerator:
    """
    Gemini 2.5 Flash Image (Nano Banana) API를 사용한 AI 이미지 생성
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
    
    def generate_image_base64(self, prompt: str) -> Optional[str]:
        """
        주제에 맞는 이미지를 AI로 생성하고 base64 데이터 반환
        Blogger에는 base64 이미지를 직접 삽입 가능
        """
        if not self.client:
            return None
            
        try:
            # Gemini 2.5 Flash Image (Nano Banana) 모델로 이미지 생성
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[f"Generate a high quality, professional blog illustration about: {prompt}. Style: modern, clean, tech-focused."],
            )
            
            # response에서 이미지 데이터 추출
            for part in response.parts:
                if part.inline_data is not None:
                    # base64 인코딩된 이미지 데이터
                    image_data = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/png"
                    
                    # base64 데이터 URL 형식으로 반환
                    return f"data:{mime_type};base64,{image_data}"
            
            return None
            
        except Exception as e:
            print(f"이미지 생성 오류: {e}")
            return None
    
    def generate_image_html(self, prompt: str, alt_text: str = "AI 생성 이미지") -> str:
        """이미지 HTML 태그 생성"""
        image_data = self.generate_image_base64(prompt)
        
        if image_data:
            return f'<p><img src="{image_data}" alt="{alt_text}" style="width:100%; max-width:800px; border-radius:8px;"></p>'
        else:
            # 이미지 생성 실패 시 placeholder 사용
            import random
            seed = random.randint(1, 1000)
            fallback_url = f"https://picsum.photos/seed/{seed}/800/450"
            return f'<p><img src="{fallback_url}" alt="{alt_text}" style="width:100%; max-width:800px; border-radius:8px;"></p>'
