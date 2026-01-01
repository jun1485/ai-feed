import os
import base64
import requests
import random
from typing import Optional
from google import genai
from google.genai import types

class ImageGenerator:
    """
    Imagen 3 이미지 생성 + ImgBB 업로드
    고품질 AI 이미지 생성 (16:9 비율, 텍스트 없음)
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
            print("[DEBUG] Gemini client가 없음 - fallback")
            return self._get_fallback_url()
        
        try:
            print(f"[DEBUG] Imagen 3 이미지 생성 시도: {prompt[:50]}...")
            
            # 블로그용 프롬프트 최적화
            optimized_prompt = f"Professional digital illustration for tech blog article about: {prompt}. Modern, clean design with vibrant colors. NO text, NO words, NO letters, NO typography. Pure visual artwork only."
            
            # Imagen 3로 이미지 생성
            response = self.client.models.generate_images(
                model="imagen-3.0-generate-001",
                prompt=optimized_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="16:9",  # 블로그에 최적화된 비율
                    person_generation="dont_allow",  # 사람 이미지 제외 (저작권 이슈 방지)
                )
            )
            
            print(f"[DEBUG] Imagen 3 Response 받음")
            
            # 생성된 이미지 처리
            if response.generated_images:
                generated_image = response.generated_images[0]
                image_data = generated_image.image.image_bytes
                
                print(f"[DEBUG] 이미지 데이터 크기: {len(image_data)} bytes")
                
                # base64 인코딩
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                # ImgBB에 업로드
                if self.imgbb_key:
                    upload_url = self._upload_to_imgbb(image_base64)
                    if upload_url:
                        print(f"[DEBUG] ImgBB 업로드 성공: {upload_url}")
                        return upload_url
                    else:
                        print("[DEBUG] ImgBB 업로드 실패")
                else:
                    print("[DEBUG] ImgBB 키 없음")
            
            print("[DEBUG] 이미지 생성 실패 - fallback")
            return self._get_fallback_url()
            
        except Exception as e:
            print(f"[DEBUG] Imagen 3 오류: {type(e).__name__}: {e}")
            return self._get_fallback_url()
    
    def _upload_to_imgbb(self, image_base64: str) -> Optional[str]:
        """ImgBB에 base64 이미지 업로드 (30일 후 자동 삭제)"""
        try:
            url = "https://api.imgbb.com/1/upload"
            payload = {
                "key": self.imgbb_key,
                "image": image_base64,
                "expiration": 2592000,
            }
            response = requests.post(url, data=payload)
            
            print(f"[DEBUG] ImgBB 응답 코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                return result.get("data", {}).get("url")
            else:
                print(f"[DEBUG] ImgBB 에러: {response.text[:200]}")
                return None
        except Exception as e:
            print(f"[DEBUG] ImgBB 오류: {e}")
            return None
    
    def _get_fallback_url(self) -> str:
        """Fallback: Lorem Picsum 무료 이미지"""
        seed = random.randint(1, 1000)
        return f"https://picsum.photos/seed/{seed}/800/450"
    
    def generate_image_html(self, prompt: str, alt_text: str = "AI 생성 이미지") -> str:
        """이미지 HTML 태그 생성"""
        image_url = self.generate_and_upload(prompt)
        return f'<p><img src="{image_url}" alt="{alt_text}" style="width:100%; max-width:800px; border-radius:8px;"></p>'
