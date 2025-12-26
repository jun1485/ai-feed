import requests

response = requests.post('https://oauth2.googleapis.com/token', data={
    'client_id': '1051190155640-61pcnrj37cjnpmf79jffadkkhpk1tgfg.apps.googleusercontent.com',
    'client_secret': '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',
    'code': '4/0ATX87lN3Hj3ryUBOhHwgNyXJ9_VvJ9IiexZZOxORviCZvclXGWtfu9LjwUcvyoWlHw4W-g',
    'grant_type': 'authorization_code',
    'redirect_uri': 'http://localhost:8888/callback'
})

result = response.json()

# 결과를 파일로 저장
with open('token_result.txt', 'w') as f:
    if 'refresh_token' in result:
        f.write("SUCCESS!\n")
        f.write(f"REFRESH_TOKEN={result['refresh_token']}\n")
    else:
        f.write(f"ERROR: {result}\n")

print("Result saved to token_result.txt")
