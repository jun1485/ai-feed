import requests
import os
import base64
from typing import Dict, Any

class WordPressPublisher:
    def __init__(self):
        self.wp_url = os.getenv("WORDPRESS_URL")
        self.user = os.getenv("WORDPRESS_USER")
        self.password = os.getenv("WORDPRESS_APP_PASSWORD")
        
    def post_article(self, article_data: Dict[str, Any], status: str = "draft") -> str:
        if not all([self.wp_url, self.user, self.password]):
            return "Skipped (No Credentials)"

        credentials = f"{self.user}:{self.password}"
        token = base64.b64encode(credentials.encode()).decode()
        headers = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}
        api_url = f"{self.wp_url.rstrip('/')}/wp-json/wp/v2/posts"
        
        payload = {
            "title": article_data.get("title"),
            "content": article_data.get("content"),
            "status": status,
        }

        try:
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json().get('link')
        except Exception as e:
            return f"Error: {e}"
