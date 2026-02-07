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
                
                # 한국어 버전 발행
                print(f"  🇰🇷 Korean version...")
                processed_ko = processor.process_content(item, language="ko")
                
                if processed_ko.get("meta_description"):
                    print(f"  📋 Meta (KR): {processed_ko['meta_description'][:50]}...")
                
                link_ko = publisher.post_article(processed_ko, is_draft=False)
                print(f"  ✅ KR Result: {link_ko}")
                
                if link_ko and not link_ko.startswith("Error") and not link_ko.startswith("Skipped"):
                    processor.add_recent_post(processed_ko["title"], link_ko)
                    published_posts.append({
                        "title": processed_ko["title"],
                        "url": link_ko,
                        "language": "ko"
                    })
                
                # 영어 버전 발행 (에드센스 승인 전까지 비활성화 - 단일 언어 품질 집중)
                # print(f"  🇺🇸 English version...")
                # processed_en = processor.process_content(item, language="en")
                #
                # if processed_en.get("meta_description"):
                #     print(f"  📋 Meta (EN): {processed_en['meta_description'][:50]}...")
                #
                # link_en = publisher.post_article(processed_en, is_draft=False)
                # print(f"  ✅ EN Result: {link_en}")
                #
                # if link_en and not link_en.startswith("Error") and not link_en.startswith("Skipped"):
                #     processor.add_recent_post(processed_en["title"], link_en)
                #     published_posts.append({
                #         "title": processed_en["title"],
                #         "url": link_en,
                #         "language": "en"
                #     })
                    
        except Exception as e:
            print(f"❌ Error with {type(crawler).__name__}: {e}")
    
    print(f"\n=== Finished: {len(published_posts)} posts published ===")
    
    # 발행된 글 목록 출력
    if published_posts:
        print("\n📚 Published posts:")
        for post in published_posts:
            lang_emoji = "🇰🇷" if post.get("language") == "ko" else "🇺🇸"
            print(f"  {lang_emoji} {post['title']}")
            print(f"     {post['url']}")

if __name__ == "__main__":
    main()
