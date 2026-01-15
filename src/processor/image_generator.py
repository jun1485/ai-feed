import os
import base64
import requests
import random
from typing import Optional
from google import genai
from google.genai import types

class ImageGenerator:
    """
    Gemini 2.0 Flash 이미지 생성 + ImgBB 업로드
    (Imagen 3는 Billing 필요 - 활성화 시 전환 가능)
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.imgbb_key = os.getenv("IMGBB_API_KEY")
        
        # Imagen 3 활성화 여부 (환경변수 또는 기본값)
        # 비용 문제로 인해 선택적으로 사용할 수 있도록 함
        self.use_imagen3 = os.getenv("USE_IMAGEN_3", "true").lower() == "true"
        
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
    
    def generate_and_upload(self, prompt: str) -> Optional[str]:
        """
        이미지 생성 후 ImgBB에 업로드하여 URL 반환
        설정에 따라 Imagen 3 또는 Gemini 2.0 Flash 사용
        """
        if not self.client:
            print("[DEBUG] Gemini client가 없음 - fallback")
            return self._get_fallback_url()
        
        # 1. Imagen 3 시도 (활성화된 경우)
        if self.use_imagen3:
            try:
                print(f"[DEBUG] Imagen 3 이미지 생성 시도: {prompt[:50]}...")
                return self._generate_with_imagen3(prompt)
            except Exception as e:
                print(f"[DEBUG] Imagen 3 생성 실패 (Fallback 시도): {e}")
                # 실패 시 Gemini 2.0 Flash로 넘어감
        
        # 2. Gemini 2.0 Flash (Fallback)
        return self._generate_with_gemini_flash(prompt)
    
    def _generate_with_imagen3(self, prompt: str) -> Optional[str]:
        """Imagen 3 모델을 사용한 고품질 이미지 생성"""
        # Imagen 3용 프롬프트 최적화 (Clean & Descriptive)
        enhanced_prompt = f"high quality, professional digital illustration for a tech blog, {prompt}, vibrant colors, sharp details, photorealistic 8k, distinct visual style, no text, no typography"
        
        try:
            # Imagen 3 생성 요청
            response = self.client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=enhanced_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="16:9",  # 블로그용 와이드 비율
                    include_rai_reason=True
                )
            )
            
            if response.generated_images:
                image_data = response.generated_images[0].image
                
                # google-genai SDK의 GeneratedImage 객체에서 bytes 추출
                # (보통 .image_bytes 또는 .image 속성이 bytes임)
                if hasattr(image_data, 'image_bytes'):
                     image_bytes = image_data.image_bytes
                else:
                    # 바로 bytes인 경우
                    image_bytes = image_data
                
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                print(f"[DEBUG] Imagen 3 생성 성공 (Base64: {len(image_base64)})")
                
                if self.imgbb_key:
                    return self._upload_to_imgbb(image_base64)
            
            print("[DEBUG] Imagen 3 생성 결과 없음")
            return None
            
        except Exception as e:
            # 권한/빌링 문제일 수 있음
            raise e

    def _generate_with_gemini_flash(self, prompt: str) -> Optional[str]:
        """Gemini 2.0 Flash를 사용한 이미지 생성 (무료/실험적)"""
        try:
            print(f"[DEBUG] Gemini 2.0 Flash 이미지 생성 시도: {prompt[:50]}...")
            
            # Gemini 2.0 Flash로 이미지 생성 요청
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=f"Generate a clean, professional, high-quality digital illustration for a tech blog about: {prompt}. Modern design with vibrant colors. IMPORTANT: Do NOT include any text, words, letters, or typography in the image. Pure visual artwork only.",
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                )
            )
            
            print(f"[DEBUG] Response 받음: {type(response)}")
            
            # 응답에서 이미지 찾기
            if response.candidates:
                for candidate in response.candidates:
                    if candidate.content and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'inline_data') and part.inline_data:
                                print(f"[DEBUG] inline_data 발견! mime_type: {part.inline_data.mime_type}")
                                
                                image_data = part.inline_data.data
                                
                                # bytes인 경우 base64로 인코딩
                                if isinstance(image_data, bytes):
                                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                                else:
                                    image_base64 = str(image_data)
                                
                                print(f"[DEBUG] Base64 길이: {len(image_base64)}")
                                
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
            
            print("[DEBUG] Gemini 2.0 Flash 이미지 파트를 찾지 못함")
            return self._get_fallback_url()
            
        except Exception as e:
            print(f"[DEBUG] Gemini 2.0 Flash 생성 오류: {e}")
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
                url = result.get("data", {}).get("url")
                print(f"[DEBUG] ImgBB 업로드 완료: {url}")
                return url
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
        # 이미지 설명에 (Generated with Imagen 3) 같은 주석은 달지 않음 (사용자 요청 없음)
        return f'<p><img src="{image_url}" alt="{alt_text}" style="width:100%; max-width:800px; border-radius:8px;"></p>'
