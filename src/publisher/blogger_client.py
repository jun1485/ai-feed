import requests
import os
from typing import Dict, Any

class BloggerPublisher:
    """
    Google Blogger API v3를 사용한 포스팅 클라이언트
    API 문서: https://developers.google.com/blogger/docs/3.0/using
    """
    
    API_BASE = "https://www.googleapis.com/blogger/v3"
    
    def __init__(self):
        self.api_key = os.getenv("BLOGGER_API_KEY")
        self.blog_id = os.getenv("BLOGGER_BLOG_ID")
        self.access_token = os.getenv("BLOGGER_ACCESS_TOKEN")
        
    def post_article(self, article_data: Dict[str, Any], is_draft: bool = True) -> str:
        """
        Blogger에 글을 발행합니다.
        
        article_data: { 'title', 'content', 'tags' }
        is_draft: True=임시저장, False=공개
        
        Returns: 발행된 글의 URL 또는 에러 메시지
        """
        if not all([self.blog_id, self.access_token]):
            print("Blogger 인증 정보가 없습니다.")
            return "Skipped (No Credentials)"
        
        # 태그를 labels로 변환
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
        
        # isDraft 파라미터로 임시저장/공개 결정
        url = f"{self.API_BASE}/blogs/{self.blog_id}/posts?isDraft={str(is_draft).lower()}"
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                result = response.json()
                post_url = result.get("url", "")
                print(f"Blogger 발행 성공: {post_url}")
                return post_url
            else:
                error_msg = response.text
                print(f"Blogger 발행 실패: {response.status_code} - {error_msg}")
                return f"Error: {response.status_code}"
                
        except Exception as e:
            print(f"Blogger API 오류: {e}")
            return f"Error: {e}"
