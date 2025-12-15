import os
import google.generativeai as genai
import base64
import requests
from typing import Optional

class ImageGenerator:
    """
    Gemini/Imagen API를 사용한 이미지 생성기
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            
    def generate_image_url(self, prompt: str) -> Optional[str]:
        """
        주제에 맞는 이미지를 생성하고 URL 반환
        Blogger는 외부 이미지 URL을 지원하므로 placeholder 이미지 사용
        실제 Imagen API가 활성화되면 교체 가능
        """
        if not self.api_key:
            return None
            
        # 현재 Gemini API의 무료 이미지 생성은 제한적
        # 대안: Unsplash API (무료) 또는 Placeholder 사용
        # 키워드 기반 무료 이미지 검색
        try:
            # Unsplash Source (무료, API 키 불필요)
            # 프롬프트에서 핵심 키워드 추출
            keywords = self._extract_keywords(prompt)
            image_url = f"https://source.unsplash.com/800x400/?{keywords}"
            return image_url
        except Exception as e:
            print(f"이미지 생성 오류: {e}")
            return None
    
    def _extract_keywords(self, text: str) -> str:
        """텍스트에서 이미지 검색용 키워드 추출"""
        # 간단한 키워드 매핑
        tech_keywords = {
            "AI": "artificial,intelligence,robot",
            "GPT": "ai,technology,computer",
            "data center": "server,datacenter,technology",
            "robot": "robot,automation",
            "machine learning": "ai,neural,network",
            "blockchain": "blockchain,crypto,technology",
            "startup": "startup,business,office",
            "google": "google,technology,office",
            "apple": "apple,technology,device",
            "microsoft": "microsoft,technology,computer",
        }
        
        text_lower = text.lower()
        for key, value in tech_keywords.items():
            if key.lower() in text_lower:
                return value
        
        return "technology,innovation,future"
