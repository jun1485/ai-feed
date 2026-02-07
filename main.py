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
    """1회 실행 시 1개 글만 발행 (8시간 간격 스케줄링 전제)"""
    print("=== AI Feed: 단일 글 발행 시작 ===")

    # 크롤러 목록에서 랜덤 1개 선택 (소스 다양성 확보)
    all_crawlers = [
        HackerNewsCrawler(),
        TechCrunchCrawler(),
        TheVergeCrawler(),
        WiredCrawler(),
        ArsTechnicaCrawler(),
        VentureBeatCrawler(),
    ]
    crawler = random.choice(all_crawlers)
    print(f"선택된 소스: {type(crawler).__name__}")

    processor = ContentProcessor()
    publisher = BloggerPublisher()

    try:
        items = crawler.fetch_latest(limit=1)
        if not items:
            print("크롤링 결과 없음 - 종료")
            return

        item = items[0]
        print(f"기사: {item['title']}")

        # 한국어 버전 발행
        processed = processor.process_content(item, language="ko")

        if processed.get("meta_description"):
            print(f"메타: {processed['meta_description'][:60]}...")

        link = publisher.post_article(processed, is_draft=False)
        print(f"결과: {link}")

        if link and not link.startswith("Error") and not link.startswith("Skipped"):
            print(f"\n발행 완료: {processed['title']}")
            print(f"URL: {link}")
        else:
            print(f"\n발행 실패: {link}")

        # 영어 버전 발행 (에드센스 승인 전까지 비활성화 - 단일 언어 품질 집중)
        # processed_en = processor.process_content(item, language="en")
        # link_en = publisher.post_article(processed_en, is_draft=False)

    except Exception as e:
        print(f"오류 발생: {e}")

    print("\n=== 완료 ===")


if __name__ == "__main__":
    main()
