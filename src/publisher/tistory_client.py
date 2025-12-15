import requests
import os
from typing import Dict, Any

class TistoryPublisher:
    """
    티스토리 Open API를 사용한 포스팅 클라이언트
    API 문서: https://tistory.github.io/document-tistory-apis/
    """
    
    API_BASE = "https://www.tistory.com/apis"
    
    def __init__(self):
        self.access_token = os.getenv("TISTORY_ACCESS_TOKEN")
        self.blog_name = os.getenv("TISTORY_BLOG_NAME")  # 예: myblog (myblog.tistory.com)
        
    def post_article(self, article_data: Dict[str, Any], visibility: str = "0") -> str:
        """
        티스토리에 글을 발행합니다.
        
        article_data: { 'title', 'content', 'tags' }
        visibility: "0"=비공개, "1"=보호, "3"=공개
        
        Returns: 발행된 글의 URL 또는 에러 메시지
        """
        if not all([self.access_token, self.blog_name]):
            print("티스토리 인증 정보가 없습니다.")
            return "Skipped (No Credentials)"
        
        # 태그를 쉼표로 연결
        tags = ",".join(article_data.get("tags", []))
        
        payload = {
            "access_token": self.access_token,
            "output": "json",
            "blogName": self.blog_name,
            "title": article_data.get("title"),
            "content": article_data.get("content"),
            "visibility": visibility,  # 0: 비공개, 3: 공개
            "category": "0",  # 0 = 기본 카테고리
            "tag": tags,
        }
        
        try:
            response = requests.post(f"{self.API_BASE}/post/write", data=payload)
            result = response.json()
            
            if result.get("tistory", {}).get("status") == "200":
                post_id = result["tistory"]["postId"]
                url = f"https://{self.blog_name}.tistory.com/{post_id}"
                print(f"티스토리 발행 성공: {url}")
                return url
            else:
                error_msg = result.get("tistory", {}).get("error_message", "Unknown error")
                print(f"티스토리 발행 실패: {error_msg}")
                return f"Error: {error_msg}"
                
        except Exception as e:
            print(f"티스토리 API 오류: {e}")
            return f"Error: {e}"
