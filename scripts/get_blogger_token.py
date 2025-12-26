#!/usr/bin/env python3
"""
Blogger OAuth Token Generator
=============================
이 스크립트를 실행하면 브라우저가 열리고 Google 로그인 후 
새로운 Refresh Token을 발급받을 수 있습니다.

사용법:
    python scripts/get_blogger_token.py

필요한 환경변수 (.env 파일):
    BLOGGER_CLIENT_ID=your_client_id
    BLOGGER_CLIENT_SECRET=your_client_secret
"""

import os
import sys
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
import json

# 프로젝트 루트 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# OAuth 설정
CLIENT_ID = os.getenv("BLOGGER_CLIENT_ID")
CLIENT_SECRET = os.getenv("BLOGGER_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8888/callback"
SCOPES = "https://www.googleapis.com/auth/blogger"

# 전역 변수로 authorization code 저장
auth_code = None

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """OAuth 콜백을 처리하는 HTTP 핸들러"""
    
    def do_GET(self):
        global auth_code
        
        parsed = urlparse(self.path)
        if parsed.path == "/callback":
            params = parse_qs(parsed.query)
            
            if "code" in params:
                auth_code = params["code"][0]
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write("""
                    <html>
                    <head><title>인증 성공!</title></head>
                    <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                        <h1>✅ 인증 성공!</h1>
                        <p>이 창을 닫고 터미널을 확인하세요.</p>
                    </body>
                    </html>
                """.encode("utf-8"))
            else:
                error = params.get("error", ["Unknown error"])[0]
                self.send_response(400)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"""
                    <html>
                    <head><title>인증 실패</title></head>
                    <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                        <h1>❌ 인증 실패</h1>
                        <p>에러: {error}</p>
                    </body>
                    </html>
                """.encode("utf-8"))
    
    def log_message(self, format, *args):
        # 서버 로그 숨기기
        pass


def get_authorization_url():
    """OAuth 인증 URL 생성"""
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent"  # 항상 refresh token 받도록
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"


def exchange_code_for_tokens(code):
    """Authorization code를 토큰으로 교환"""
    response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI
        }
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ 토큰 교환 실패: {response.text}")
        return None


def main():
    global auth_code
    
    print("=" * 50)
    print("🔐 Blogger OAuth Token Generator")
    print("=" * 50)
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ 환경변수가 설정되지 않았습니다!")
        print("   .env 파일에 BLOGGER_CLIENT_ID와 BLOGGER_CLIENT_SECRET을 설정하세요.")
        return
    
    # 1. 로컬 서버 시작
    print("\n📡 로컬 서버 시작 (port 8888)...")
    server = HTTPServer(("localhost", 8888), OAuthCallbackHandler)
    
    # 2. 브라우저에서 인증 페이지 열기
    auth_url = get_authorization_url()
    print("🌐 브라우저에서 Google 로그인 페이지를 엽니다...")
    print(f"\n📋 URL (브라우저가 안 열리면 수동으로 접속):\n{auth_url}\n")
    
    # Windows에서 브라우저 열기
    if sys.platform == "win32":
        os.system(f'start "" "{auth_url}"')
    else:
        webbrowser.open(auth_url)
    
    # 3. 콜백 대기
    print("⏳ 인증 완료 대기 중... (브라우저에서 로그인하세요)")
    
    while auth_code is None:
        server.handle_request()
    
    server.server_close()
    
    # 4. 토큰 교환
    print("\n🔄 토큰 교환 중...")
    tokens = exchange_code_for_tokens(auth_code)
    
    if tokens:
        print("\n" + "=" * 50)
        print("✅ 성공! 새로운 토큰을 발급받았습니다!")
        print("=" * 50)
        
        refresh_token = tokens.get("refresh_token")
        access_token = tokens.get("access_token")
        
        if refresh_token:
            print(f"\n📋 REFRESH TOKEN (GitHub Secrets에 저장):")
            print("-" * 50)
            print(refresh_token)
            print("-" * 50)
            
            print("\n📝 다음 단계:")
            print("1. GitHub Repository Settings → Secrets and variables → Actions")
            print("2. BLOGGER_REFRESH_TOKEN 값을 위의 토큰으로 업데이트")
            print("3. 다시 workflow 실행!")
            
            # .env 파일 업데이트 제안
            print("\n💡 로컬 테스트용 .env 파일도 업데이트할까요? (y/n): ", end="")
            answer = input().strip().lower()
            
            if answer == "y":
                update_env_file(refresh_token)
        else:
            print("⚠️ Refresh Token이 없습니다!")
            print("   Google Cloud Console에서 OAuth 동의 화면을 확인하세요.")
            print("   '테스트' 모드인 경우 '프로덕션'으로 변경하거나,")
            print("   access_type=offline, prompt=consent 옵션을 확인하세요.")


def update_env_file(refresh_token):
    """로컬 .env 파일 업데이트"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
        
        updated = False
        new_lines = []
        for line in lines:
            if line.startswith("BLOGGER_REFRESH_TOKEN="):
                new_lines.append(f"BLOGGER_REFRESH_TOKEN={refresh_token}\n")
                updated = True
            else:
                new_lines.append(line)
        
        if not updated:
            new_lines.append(f"BLOGGER_REFRESH_TOKEN={refresh_token}\n")
        
        with open(env_path, "w") as f:
            f.writelines(new_lines)
        
        print("✅ .env 파일이 업데이트되었습니다!")
    else:
        print("⚠️ .env 파일이 없습니다. 수동으로 생성하세요.")


if __name__ == "__main__":
    main()
