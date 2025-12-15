import praw
import os
from typing import List, Dict, Any
from .base import BaseCrawler
import datetime

class RedditCrawler(BaseCrawler):
    def __init__(self):
        try:
            self.reddit = praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID"),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                user_agent="ai-feed-bot/1.0"
            )
        except Exception as e:
            print(f"Warning: Reddit credentials not found. {e}")
            self.reddit = None

    def fetch_latest(self, limit: int = 5) -> List[Dict[str, Any]]:
        if not self.reddit:
            return []

        print("Fetching Reddit top posts...")
        subreddits = ["MachineLearning", "ArtificialInteligence"]
        results = []
        try:
            subreddit = self.reddit.subreddit("+".join(subreddits))
            for post in subreddit.hot(limit=limit):
                if post.stickied: continue
                results.append({
                    'title': post.title,
                    'url': post.url,
                    'original_content': post.selftext if post.is_self else post.title,
                    'source': f"Reddit (r/{post.subreddit.display_name})",
                    'timestamp': datetime.datetime.fromtimestamp(post.created_utc).isoformat()
                })
        except Exception as e:
            print(f"Error: {e}")
        return results
