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
    print("=== AI Feed Automation Started (SEO Optimized) ===")
    
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
    
    # 성공적으로 발행된 글 목록 (내부 링크용)
    published_posts = []
    
    for crawler in selected_crawlers:
        try:
            items = crawler.fetch_latest(limit=1)  # 소스당 1개씩
            for item in items:
                print(f"\n📝 Processing: {item['title']}")
                
                # 콘텐츠 처리 (SEO 최적화 적용)
                processed = processor.process_content(item)
                
                # 메타 설명 출력 (디버그용)
                if processed.get("meta_description"):
                    print(f"📋 Meta: {processed['meta_description'][:50]}...")
                
                # 발행
                link = publisher.post_article(processed, is_draft=False)
                print(f"✅ Result: {link}")
                
                # 발행 성공 시 내부 링크 목록에 추가
                if link and not link.startswith("Error") and not link.startswith("Skipped"):
                    processor.add_recent_post(processed["title"], link)
                    published_posts.append({
                        "title": processed["title"],
                        "url": link
                    })
                    
        except Exception as e:
            print(f"❌ Error with {type(crawler).__name__}: {e}")
    
    print(f"\n=== Finished: {len(published_posts)} posts published ===")
    
    # 발행된 글 목록 출력
    if published_posts:
        print("\n📚 Published posts:")
        for post in published_posts:
            print(f"  - {post['title']}")
            print(f"    {post['url']}")

if __name__ == "__main__":
    main()
