"""
OAuth Token 교환 스크립트 (예시)
실제 사용 시 .env 파일에서 환경변수를 로드하세요.

사용법:
1. .env 파일에 BLOGGER_CLIENT_ID, BLOGGER_CLIENT_SECRET 설정
2. get_blogger_token.py 스크립트로 인증 진행
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# 환경변수에서 로드 (절대 하드코딩 금지!)
CLIENT_ID = os.getenv('BLOGGER_CLIENT_ID')
CLIENT_SECRET = os.getenv('BLOGGER_CLIENT_SECRET')

# 사용 예시 (실제 코드는 .env에서 가져와야 함)
print("이 스크립트는 예시입니다.")
print("실제 토큰 발급은 get_blogger_token.py를 사용하세요.")
