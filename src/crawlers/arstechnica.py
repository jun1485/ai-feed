import feedparser
from typing import List, Dict, Any

class ArsTechnicaCrawler:
    """Ars Technica AI RSS 크롤러"""
    
    def fetch_latest(self, limit: int = 2) -> List[Dict[str, Any]]:
        print("Fetching Ars Technica AI feed...")
        feed = feedparser.parse("https://feeds.arstechnica.com/arstechnica/technology-lab")
        
        items = []
        for entry in feed.entries[:limit]:
            items.append({
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "original_content": entry.get("summary", ""),
                "source": "Ars Technica"
            })
        return items
