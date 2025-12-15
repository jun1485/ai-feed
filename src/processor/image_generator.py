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
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.imgbb_key = os.getenv("IMGBB_API_KEY")
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
    
    def generate_and_upload(self, prompt: str) -> Optional[str]:
        """
        Gemini로 이미지 생성 후 ImgBB에 업로드하여 URL 반환
        """
        if not self.client:
            print("[DEBUG] Gemini client가 없음 - fallback")
            return self._get_fallback_url()
        
        try:
            print(f"[DEBUG] 이미지 생성 시도: {prompt[:50]}...")
            
            # Gemini 2.0 Flash로 이미지 생성 요청
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=f"Generate a clean, professional illustration for a tech blog about: {prompt}. IMPORTANT: Do NOT include any text, words, letters, or typography in the image. Pure visual illustration only.",
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
                            print(f"[DEBUG] Part type: {type(part)}")
                            
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
                            
                            elif hasattr(part, 'text'):
                                print(f"[DEBUG] Text part: {part.text[:100] if part.text else 'empty'}...")
            
            print("[DEBUG] 이미지 파트를 찾지 못함 - fallback")
            return self._get_fallback_url()
            
        except Exception as e:
            print(f"[DEBUG] 이미지 생성 오류: {type(e).__name__}: {e}")
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
