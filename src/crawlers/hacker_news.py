import requests
from typing import List, Dict, Any
from .base import BaseCrawler
import datetime

class HackerNewsCrawler(BaseCrawler):
    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def fetch_latest(self, limit: int = 5) -> List[Dict[str, Any]]:
        print("Fetching Hacker News top stories...")
        try:
            resp = requests.get(f"{self.BASE_URL}/topstories.json")
            resp.raise_for_status()
            story_ids = resp.json()[:limit*2]
        except Exception as e:
            print(f"Error fetching HN IDs: {e}")
            return []

        results = []
        for sid in story_ids:
            if len(results) >= limit:
                break
            try:
                item_resp = requests.get(f"{self.BASE_URL}/item/{sid}.json")
                item = item_resp.json()
                if item.get('type') == 'story' and 'url' in item:
                    results.append({
                        'title': item.get('title'),
                        'url': item.get('url'),
                        'original_content': item.get('title'),
                        'source': 'Hacker News',
                        'timestamp': datetime.datetime.fromtimestamp(item.get('time', 0)).isoformat()
                    })
            except Exception:
                continue
        return results
