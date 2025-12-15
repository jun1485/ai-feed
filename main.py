import os
import random
from dotenv import load_dotenv
from src.crawlers.hacker_news import HackerNewsCrawler
from src.crawlers.techcrunch import TechCrunchCrawler
from src.crawlers.theverge import TheVergeCrawler
from src.crawlers.wired import WiredCrawler
from src.crawlers.arstechnica import ArsTechnicaCrawler
from src.crawlers.venturebeat import VentureBeatCrawler
from src.processor.llm_rewriter import ContentProcessor
from src.publisher.blogger_client import BloggerPublisher

load_dotenv()

def main():
    print("=== AI Feed Automation Started ===")
    
    # 모든 크롤러 목록
    all_crawlers = [
        HackerNewsCrawler(),
        TechCrunchCrawler(),
        TheVergeCrawler(),
        WiredCrawler(),
        ArsTechnicaCrawler(),
        VentureBeatCrawler(),
    ]
    
    # 랜덤으로 3개 소스 선택 (다양성 확보)
    selected_crawlers = random.sample(all_crawlers, min(3, len(all_crawlers)))
    print(f"Selected sources: {[type(c).__name__ for c in selected_crawlers]}")
    
    processor = ContentProcessor()
    publisher = BloggerPublisher()
    
    for crawler in selected_crawlers:
        try:
            items = crawler.fetch_latest(limit=1)  # 소스당 1개씩
            for item in items:
                print(f"Processing: {item['title']}")
                processed = processor.process_content(item)
                link = publisher.post_article(processed, is_draft=False)
                print(f"Result: {link}")
        except Exception as e:
            print(f"Error with {type(crawler).__name__}: {e}")

    print("=== Finished ===")

if __name__ == "__main__":
    main()
