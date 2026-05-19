import os
import time
import json
import csv
import shutil
import base64
import io
import unicodedata
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from PIL import Image
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler
from openai import OpenAI
from dotenv import load_dotenv

# =========================================
# 1. 初期設定（ディレクトリと設定読み込み）
# =========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, '1_Input')
OUTPUT_DIR = os.path.join(BASE_DIR, '2_Output')
MASTER_CSV_PATH = os.path.join(OUTPUT_DIR, "adobe_stock_master.csv")

# .env から安全にキーを読み込む
load_dotenv(os.path.join(BASE_DIR, '.env'))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("エラー: .env ファイルに OPENAI_API_KEY が設定されていません。")
    exit()

client = OpenAI(api_key=OPENAI_API_KEY)
executor = ThreadPoolExecutor(max_workers=3) 
csv_lock = threading.Lock()

# =========================================
# 2. メタデータ生成ロジック
# =========================================
def generate_metadata(img_path):
    filename = unicodedata.normalize('NFC', os.path.basename(img_path))
    
    try:
        with Image.open(img_path) as img:
            if img.mode != 'RGB': img = img.convert('RGB')
            if max(img.size) > 1024:
                img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

        prompt = """
        Analyze this image and provide:
        1. A catchy title (max 70 chars, no commas).
        2. Exactly 50 highly relevant SEO keywords (comma-separated).
        
        Rules:
        - Use these 8 perspectives: Subject, Background, Color, Emotion, Technique, Concept, Season, Use-case.
        - Output ONLY a JSON object: {"title": "...", "keywords": "k1, k2, ..."}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={ "type": "json_object" },
            messages=[{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}", "detail": "low"}}
            ]}]
        )
        
        data = json.loads(response.choices[0].message.content)
        title = data.get('title', 'Untitled').replace(',', '')
        keywords = data.get('keywords', '')

        # CSVに書き込み（スレッドセーフ ＋ 強制物理保存版）
        with csv_lock:
            file_exists = os.path.isfile(MASTER_CSV_PATH)
            with open(MASTER_CSV_PATH, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, lineterminator='\n')
                if not file_exists:
                    writer.writerow(['Filename', 'Title', 'Keywords'])
                writer.writerow([filename, title, keywords])
                f.flush()            # メモリからOSへ
                os.fsync(f.fileno())  # OSからディスクへ（これで全ロスを防ぐ）

        shutil.move(img_path, os.path.join(OUTPUT_DIR, filename))
        print(f"[{datetime.now()}] 成功: {filename}")

    except Exception as e:
        print(f"[{datetime.now()}] エラー: {filename} - {e}")

# =========================================
# 3. 監視システム
# =========================================
class ImageHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.jpg', '.jpeg')):
            time.sleep(1)
            executor.submit(generate_metadata, event.src_path)

if __name__ == "__main__":
    for d in [INPUT_DIR, OUTPUT_DIR]:
        if not os.path.exists(d): os.makedirs(d)
    
    print(f"監視を開始しました: {INPUT_DIR}")
    event_handler = ImageHandler()
    observer = Observer()
    observer.schedule(event_handler, INPUT_DIR, recursive=False)
    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()