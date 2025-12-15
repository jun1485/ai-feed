import os
from dotenv import load_dotenv
from src.crawlers.hacker_news import HackerNewsCrawler
from src.crawlers.techcrunch import TechCrunchCrawler
from src.crawlers.reddit import RedditCrawler
from src.processor.llm_rewriter import ContentProcessor
from src.publisher.blogger_client import BloggerPublisher

load_dotenv()

def main():
    print("=== AI Feed Automation Started ===")
    
    crawlers = [HackerNewsCrawler(), TechCrunchCrawler(), RedditCrawler()]
    processor = ContentProcessor()
    publisher = BloggerPublisher()
    
    for crawler in crawlers:
        try:
            items = crawler.fetch_latest(limit=2)
            for item in items:
                print(f"Processing: {item['title']}")
                processed = processor.process_content(item)
                # is_draft=False: 바로 게시
                link = publisher.post_article(processed, is_draft=False)
                print(f"Result: {link}")
        except Exception as e:
            print(f"Error: {e}")

    print("=== Finished ===")

if __name__ == "__main__":
    main()
