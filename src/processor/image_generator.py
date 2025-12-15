import os
import base64
import requests
import random
from typing import Optional
from google import genai
from google.genai import types

class ImageGenerator:
    """
    Gemini Imagen 3 + ImgBB 업로드
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.imgbb_key = os.getenv("IMGBB_API_KEY")
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
    
    def generate_and_upload(self, prompt: str) -> Optional[str]:
        """
        Imagen 3로 이미지 생성 후 ImgBB에 업로드하여 URL 반환
        """
        if not self.client:
            return self._get_fallback_url()
        
        try:
            # Imagen 3로 이미지 생성
            response = self.client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=f"Professional tech blog illustration about: {prompt}. Style: clean, modern, minimalist.",
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                )
            )
            
            # 생성된 이미지 추출
            if response.generated_images and len(response.generated_images) > 0:
                image = response.generated_images[0]
                image_bytes = image.image.image_bytes
                
                # bytes를 base64로 인코딩
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                print(f"이미지 생성 완료! 크기: {len(image_base64)} chars")
                
                # ImgBB에 업로드
                if self.imgbb_key:
                    upload_url = self._upload_to_imgbb(image_base64)
                    if upload_url:
                        print(f"ImgBB 업로드 성공: {upload_url}")
                        return upload_url
                
                # ImgBB 키가 없으면 fallback
                return self._get_fallback_url()
            
            print("이미지 생성 결과 없음")
            return self._get_fallback_url()
            
        except Exception as e:
            print(f"이미지 생성 오류: {e}")
            return self._get_fallback_url()
    
    def _upload_to_imgbb(self, image_base64: str) -> Optional[str]:
        """ImgBB에 base64 이미지 업로드 (30일 후 자동 삭제)"""
        try:
            url = "https://api.imgbb.com/1/upload"
            payload = {
                "key": self.imgbb_key,
                "image": image_base64,
                "expiration": 2592000,  # 30일 후 자동 삭제 (초 단위)
            }
            response = requests.post(url, data=payload)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("data", {}).get("url")
            else:
                print(f"ImgBB 업로드 실패: {response.text}")
                return None
        except Exception as e:
            print(f"ImgBB 오류: {e}")
            return None
    
    def _get_fallback_url(self) -> str:
        """Fallback: Lorem Picsum 무료 이미지"""
        seed = random.randint(1, 1000)
        return f"https://picsum.photos/seed/{seed}/800/450"
    
    def generate_image_html(self, prompt: str, alt_text: str = "AI 생성 이미지") -> str:
        """이미지 HTML 태그 생성"""
        image_url = self.generate_and_upload(prompt)
        return f'<p><img src="{image_url}" alt="{alt_text}" style="width:100%; max-width:800px; border-radius:8px;"></p>'
