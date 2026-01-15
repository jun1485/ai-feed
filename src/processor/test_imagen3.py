import os
import sys

def log(msg):
    with open("verification_log.txt", "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

log("Script started...")

try:
    from dotenv import load_dotenv
    # 프로젝트 루트 경로 추가
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.processor.image_generator import ImageGenerator
except Exception as e:
    log(f"Import Error: {e}")
    sys.exit(1)

def test_generation():
    log("Entering test_generation...")
    # 환경변수 로드
    load_dotenv()
    
    # 강제로 Imagen 3 활성화
    os.environ["USE_IMAGEN_3"] = "true"
    
    log("Initialize ImageGenerator...")
    try:
        generator = ImageGenerator()
    except Exception as e:
         log(f"Init Error: {e}")
         return
    
    prompt = "Futuristic smart city in Korea, glowing concept art, highly detailed"
    log(f"Generating image with prompt: {prompt}")
    
    try:
        url = generator.generate_and_upload(prompt)
        if url:
            log(f"SUCCESS! Image generated and uploaded: {url}")
        else:
            log("FAILED. No URL returned.")
    except Exception as e:
        log(f"ERROR during generation: {e}")

if __name__ == "__main__":
    if os.path.exists("verification_log.txt"):
        os.remove("verification_log.txt")
    test_generation()
