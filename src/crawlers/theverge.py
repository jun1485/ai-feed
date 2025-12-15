import feedparser
from typing import List, Dict, Any

class TheVergeCrawler:
    """The Verge AI/Tech RSS 크롤러"""
    
    def fetch_latest(self, limit: int = 2) -> List[Dict[str, Any]]:
        print("Fetching The Verge AI feed...")
        feed = feedparser.parse("https://www.theverge.com/rss/ai-artificial-intelligence/index.xml")
        
        items = []
        for entry in feed.entries[:limit]:
            items.append({
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "original_content": entry.get("summary", ""),
                "source": "The Verge"
            })
        return items
