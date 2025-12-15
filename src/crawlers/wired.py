import feedparser
from typing import List, Dict, Any

class WiredCrawler:
    """Wired AI/Tech RSS 크롤러"""
    
    def fetch_latest(self, limit: int = 2) -> List[Dict[str, Any]]:
        print("Fetching Wired AI feed...")
        feed = feedparser.parse("https://www.wired.com/feed/tag/ai/latest/rss")
        
        items = []
        for entry in feed.entries[:limit]:
            items.append({
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "original_content": entry.get("summary", ""),
                "source": "Wired"
            })
        return items
