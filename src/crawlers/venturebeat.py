import feedparser
from typing import List, Dict, Any

class VentureBeatCrawler:
    """VentureBeat AI RSS 크롤러"""
    
    def fetch_latest(self, limit: int = 2) -> List[Dict[str, Any]]:
        print("Fetching VentureBeat AI feed...")
        feed = feedparser.parse("https://venturebeat.com/category/ai/feed/")
        
        items = []
        for entry in feed.entries[:limit]:
            items.append({
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "original_content": entry.get("summary", ""),
                "source": "VentureBeat"
            })
        return items
