import requests
import os
from typing import Dict, Any

class BloggerPublisher:
    """
    Google Blogger API v3 - Refresh Token 지원 버전
    """
    
    API_BASE = "https://www.googleapis.com/blogger/v3"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    
    def __init__(self):
        self.blog_id = os.getenv("BLOGGER_BLOG_ID")
        self.client_id = os.getenv("BLOGGER_CLIENT_ID")
        self.client_secret = os.getenv("BLOGGER_CLIENT_SECRET")
        self.refresh_token = os.getenv("BLOGGER_REFRESH_TOKEN")
        self.access_token = None
        
        # 시작 시 Access Token 갱신
        if all([self.client_id, self.client_secret, self.refresh_token]):
            self._refresh_access_token()
    
    def _refresh_access_token(self):
        """Refresh Token을 사용하여 새 Access Token 발급"""
        try:
            response = requests.post(self.TOKEN_URL, data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token"
            })
            
            if response.status_code == 200:
                self.access_token = response.json().get("access_token")
                print("Access Token 갱신 성공!")
            else:
                print(f"Token 갱신 실패: {response.text}")
        except Exception as e:
            print(f"Token 갱신 오류: {e}")
        
    def post_article(self, article_data: Dict[str, Any], is_draft: bool = True) -> str:
        if not all([self.blog_id, self.access_token]):
            print("Blogger 인증 정보가 없습니다.")
            return "Skipped (No Credentials)"
        
        labels = article_data.get("tags", ["AI", "Tech"])
        
        payload = {
            "kind": "blogger#post",
            "title": article_data.get("title"),
            "content": article_data.get("content"),
            "labels": labels
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.API_BASE}/blogs/{self.blog_id}/posts?isDraft={str(is_draft).lower()}"
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                result = response.json()
                post_url = result.get("url", "")
                print(f"Blogger 발행 성공: {post_url}")
                return post_url
            else:
                print(f"Blogger 발행 실패: {response.status_code} - {response.text}")
                return f"Error: {response.status_code}"
                
        except Exception as e:
            print(f"Blogger API 오류: {e}")
            return f"Error: {e}"
