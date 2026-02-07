import os
import re
import requests
import random
from typing import Optional, List


class ImageGenerator:
    """
    블로그 대표 이미지 제공
    우선순위: Unsplash 검색 → Lorem Picsum fallback
    """

    def __init__(self):
        self.unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")

    def generate_and_upload(self, prompt: str) -> Optional[str]:
        """기사 주제 기반 고품질 이미지 URL 반환"""
        # 1. Unsplash 검색 (API 키 존재 시)
        if self.unsplash_key:
            url = self._search_unsplash(prompt)
            if url:
                return url

        # 2. Fallback: Lorem Picsum
        return self._get_fallback_url()

    def _extract_search_keywords(self, prompt: str) -> str:
        """기사 제목에서 Unsplash 검색용 키워드 추출"""
        # 불필요한 기호/접두사 제거
        cleaned = re.sub(r'[^\w\s\'-]', ' ', prompt)
        # 검색에 무의미한 단어 제거
        stopwords = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'can', 'shall',
            'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
            'as', 'into', 'through', 'during', 'before', 'after', 'above',
            'below', 'between', 'out', 'off', 'over', 'under', 'again',
            'further', 'then', 'once', 'that', 'this', 'these', 'those',
            'it', 'its', 'and', 'but', 'or', 'nor', 'not', 'so', 'yet',
            'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
            'no', 'only', 'own', 'same', 'than', 'too', 'very', 'just',
            'about', 'up', 'how', 'what', 'which', 'who', 'whom', 'why',
            'where', 'when', 'all', 'new', 'says', 'report', 'pushes',
            'back', 'against', 'his', 'her', 'their', 'our', 'your',
        }
        words = cleaned.lower().split()
        keywords = [w for w in words if w not in stopwords and len(w) > 2]

        # 핵심 키워드 최대 3개 + "technology" 보조 키워드
        selected = keywords[:3]
        if not any(k in {'ai', 'tech', 'technology', 'software', 'computer'} for k in selected):
            selected.append('technology')

        return ' '.join(selected)

    def _search_unsplash(self, prompt: str) -> Optional[str]:
        """Unsplash API로 주제 관련 고품질 사진 검색"""
        query = self._extract_search_keywords(prompt)
        print(f"[Unsplash] 검색 키워드: {query}")

        try:
            response = requests.get(
                "https://api.unsplash.com/search/photos",
                params={
                    "query": query,
                    "per_page": 10,
                    "orientation": "landscape",
                    "content_filter": "high",
                },
                headers={
                    "Authorization": f"Client-ID {self.unsplash_key}",
                },
                timeout=10,
            )

            if response.status_code != 200:
                print(f"[Unsplash] API 오류: {response.status_code}")
                return None

            data = response.json()
            results = data.get("results", [])

            if not results:
                print("[Unsplash] 검색 결과 없음")
                return None

            # 상위 결과 중 랜덤 선택 (다양성 확보)
            photo = random.choice(results[:5])
            # w=800 파라미터로 적절한 크기 요청
            image_url = photo["urls"]["regular"]
            photographer = photo["user"]["name"]
            print(f"[Unsplash] 이미지 선택 완료 (by {photographer})")

            return image_url

        except Exception as e:
            print(f"[Unsplash] 검색 오류: {e}")
            return None

    def _get_fallback_url(self) -> str:
        """Fallback: Lorem Picsum 무료 이미지"""
        seed = random.randint(1, 1000)
        return f"https://picsum.photos/seed/{seed}/800/450"

    def generate_image_html(self, prompt: str, alt_text: str = "AI 생성 이미지") -> str:
        """이미지 HTML 태그 생성"""
        image_url = self.generate_and_upload(prompt)
        return f'<p><img src="{image_url}" alt="{alt_text}" class="post-image"></p>'
