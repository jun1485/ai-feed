"""
쿠팡 파트너스 API 연동 모듈
=============================
AI 뉴스 글에 관련 상품을 자동으로 추천하고 제휴 링크를 삽입합니다.

API 키 발급: https://partners.coupang.com/
- 추가기능 > 파트너스 API > API 키 발급
"""

import os
import hmac
import hashlib
import time
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone


class CoupangPartnersAPI:
    """쿠팡 파트너스 API 클라이언트"""
    
    DOMAIN = "https://api-gateway.coupang.com"
    
    def __init__(self):
        self.access_key = os.getenv("COUPANG_ACCESS_KEY")
        self.secret_key = os.getenv("COUPANG_SECRET_KEY")
        self.partner_id = os.getenv("COUPANG_PARTNER_ID", "")
        
    def _generate_hmac_signature(self, method: str, url_path: str, timestamp: str) -> str:
        """HMAC 서명 생성"""
        message = f"{timestamp}{method}{url_path}"
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_authorization_header(self, method: str, url_path: str) -> Dict[str, str]:
        """인증 헤더 생성"""
        timestamp = datetime.now(timezone.utc).strftime("%y%m%dT%H%M%SZ")
        signature = self._generate_hmac_signature(method, url_path, timestamp)
        
        return {
            "Authorization": f"CEA algorithm=HmacSHA256, access-key={self.access_key}, signed-date={timestamp}, signature={signature}",
            "Content-Type": "application/json"
        }
    
    def search_products(self, keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
        """키워드로 상품 검색"""
        if not self.access_key or not self.secret_key:
            print("[쿠팡] API 키가 설정되지 않았습니다.")
            return []
        
        url_path = "/v2/providers/affiliate_open_api/apis/openapi/products/search"
        
        params = {
            "keyword": keyword,
            "limit": limit,
            "sortType": "BEST_SELLING"  # BEST_SELLING, PRICE_LOW, PRICE_HIGH
        }
        
        try:
            headers = self._get_authorization_header("GET", url_path)
            response = requests.get(
                f"{self.DOMAIN}{url_path}",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("data", {}).get("productData", [])
                return products[:limit]
            else:
                print(f"[쿠팡] API 오류: {response.status_code} - {response.text[:200]}")
                return []
                
        except Exception as e:
            print(f"[쿠팡] 요청 실패: {e}")
            return []
    
    def get_deeplink(self, product_url: str) -> Optional[str]:
        """상품 URL을 파트너스 딥링크로 변환"""
        if not self.access_key or not self.secret_key:
            return None
        
        url_path = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"
        
        payload = {
            "coupangUrls": [product_url]
        }
        
        try:
            headers = self._get_authorization_header("POST", url_path)
            response = requests.post(
                f"{self.DOMAIN}{url_path}",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                links = data.get("data", [])
                if links:
                    return links[0].get("shortenUrl")
            return None
            
        except Exception as e:
            print(f"[쿠팡] 딥링크 생성 실패: {e}")
            return None


class CoupangProductRecommender:
    """AI 글에 맞는 쿠팡 상품 추천"""
    
    # AI/테크 관련 키워드 매핑
    KEYWORD_MAPPING = {
        # AI/ChatGPT 관련
        "chatgpt": ["AI 스피커", "무선 키보드", "노트북 거치대"],
        "gpt": ["AI 스피커", "무선 키보드", "외장 SSD"],
        "openai": ["프로그래밍 입문서", "코딩 키보드", "모니터"],
        
        # 구글 관련
        "google": ["구글 네스트", "크롬캐스트", "구글 기프트카드"],
        "gemini": ["AI 스피커", "스마트워치", "무선이어폰"],
        
        # 애플 관련
        "apple": ["아이폰 케이스", "맥북 거치대", "애플워치 밴드"],
        "siri": ["에어팟", "아이폰 액세서리", "애플 기프트카드"],
        
        # 로봇/자율주행
        "robot": ["로봇청소기", "코딩 로봇", "드론"],
        "자율주행": ["블랙박스", "차량용 충전기", "차량용 거치대"],
        "tesla": ["전기차 충전기", "차량용 액세서리", "블랙박스"],
        
        # 일반 테크
        "ai": ["AI 스피커", "스마트홈", "무선 이어폰"],
        "tech": ["무선 충전기", "보조배터리", "USB 허브"],
        "반도체": ["외장 SSD", "메모리카드", "노트북"],
        "엔비디아": ["그래픽카드", "게이밍 마우스", "게이밍 키보드"],
        
        # 기본
        "default": ["무선 이어폰", "보조배터리", "USB 충전기"]
    }
    
    def __init__(self):
        self.api = CoupangPartnersAPI()
    
    def _extract_keywords(self, title: str, content: str) -> List[str]:
        """글에서 관련 키워드 추출"""
        text = (title + " " + content).lower()
        keywords = []
        
        for key in self.KEYWORD_MAPPING.keys():
            if key != "default" and key in text:
                keywords.extend(self.KEYWORD_MAPPING[key])
        
        # 키워드가 없으면 기본값 사용
        if not keywords:
            keywords = self.KEYWORD_MAPPING["default"]
        
        # 중복 제거
        return list(set(keywords))[:3]
    
    def get_product_recommendations(self, title: str, content: str = "") -> List[Dict[str, Any]]:
        """글에 맞는 상품 추천"""
        keywords = self._extract_keywords(title, content)
        
        all_products = []
        for keyword in keywords:
            products = self.api.search_products(keyword, limit=1)
            all_products.extend(products)
            
            if len(all_products) >= 3:
                break
        
        return all_products[:3]
    
    def generate_product_html(self, title: str, content: str = "") -> str:
        """상품 추천 HTML 생성"""
        api_available = self.api.access_key and self.api.secret_key
        
        if not api_available:
            # API 키가 없으면 빈 문자열 반환 (광고 없이 진행)
            return ""
        
        products = self.get_product_recommendations(title, content)
        
        if not products:
            return ""
        
        html = """
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 15px; margin: 30px 0; color: white;">
    <h3 style="margin-top: 0; font-size: 18px;">🛒 이 글과 관련된 추천 상품</h3>
    <p style="font-size: 12px; opacity: 0.8; margin-bottom: 20px;">※ 파트너스 활동으로 일정액의 수수료를 제공받을 수 있습니다.</p>
    <div style="display: flex; flex-wrap: wrap; gap: 15px;">
"""
        
        for product in products:
            name = product.get("productName", "상품")[:40]
            price = product.get("productPrice", 0)
            image = product.get("productImage", "")
            url = product.get("productUrl", "")
            
            # 딥링크 생성 시도
            affiliate_url = self.api.get_deeplink(url) or url
            
            price_formatted = f"{price:,}원" if price else "가격 확인"
            
            html += f"""
        <a href="{affiliate_url}" target="_blank" rel="noopener" style="flex: 1; min-width: 150px; max-width: 200px; background: white; border-radius: 10px; padding: 15px; text-decoration: none; color: #333; transition: transform 0.2s;">
            <img src="{image}" alt="{name}" style="width: 100%; border-radius: 8px; margin-bottom: 10px;">
            <p style="font-size: 13px; font-weight: bold; margin: 0 0 8px 0; line-height: 1.3;">{name}...</p>
            <p style="font-size: 14px; color: #e53e3e; font-weight: bold; margin: 0;">{price_formatted}</p>
        </a>
"""
        
        html += """
    </div>
</div>
"""
        return html


# 테스트용 함수 (API 키 없이도 동작 확인)
def create_fallback_product_html(keywords: List[str] = None) -> str:
    """
    API 키 없이 기본 쿠팡 검색 링크 생성
    (나중에 쿠팡 파트너스 가입 후 API 키를 발급받으면 자동으로 제휴링크로 변환됨)
    """
    if not keywords:
        keywords = ["AI 스피커", "무선이어폰", "보조배터리"]
    
    html = """
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 15px; margin: 30px 0; color: white;">
    <h3 style="margin-top: 0; font-size: 18px;">🛒 관련 추천 상품</h3>
    <p style="font-size: 12px; opacity: 0.8;">쿠팡에서 검색하기</p>
    <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px;">
"""
    
    for keyword in keywords[:3]:
        search_url = f"https://www.coupang.com/np/search?q={keyword}&channel=user&component=&eventCategory=SRP"
        html += f"""
        <a href="{search_url}" target="_blank" rel="noopener" style="background: white; color: #333; padding: 10px 20px; border-radius: 20px; text-decoration: none; font-size: 14px; font-weight: bold;">
            {keyword} 보기 →
        </a>
"""
    
    html += """
    </div>
</div>
"""
    return html
