import os
import openai
from typing import Dict, Any

class ContentProcessor:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key

    def process_content(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "title": f"[Demo] {raw_data['title']}",
                "content": f"Source: {raw_data['url']}\n\n{raw_data['original_content']}",
                "tags": ["AI"],
                "original_url": raw_data['url']
            }

        prompt = f"""
        Translate and rewrite this tech news into a Korean blog post.
        Title: {raw_data['title']}
        Content: {raw_data['original_content']}
        """

        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            content = response.choices[0].message.content
            return {
                "title": raw_data['title'],
                "content": content,
                "tags": ["AI"],
                "original_url": raw_data['url']
            }
        except Exception as e:
            return {"title": "Error", "content": str(e), "original_url": raw_data['url']}
