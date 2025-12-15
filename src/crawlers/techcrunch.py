import feedparser
from typing import List, Dict, Any
from .base import BaseCrawler
import datetime

class TechCrunchCrawler(BaseCrawler):
    RSS_URL = "https://techcrunch.com/category/artificial-intelligence/feed/"

    def fetch_latest(self, limit: int = 5) -> List[Dict[str, Any]]:
        print(f"Fetching TechCrunch AI feed...")
        feed = feedparser.parse(self.RSS_URL)
        results = []
        for entry in feed.entries[:limit]:
            results.append({
                'title': entry.title,
                'url': entry.link,
                'original_content': entry.get('summary', '') or entry.get('description', ''),
                'source': 'TechCrunch',
                'timestamp': entry.published if 'published' in entry else datetime.datetime.now().isoformat()
            })
        return results
