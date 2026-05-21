# Adobe Stock Metadata & Tag Generator API

Multi-language documentation (English / 日本語 / 繁體中文) for the Adobe Stock Metadata & Tag Generator API.

---

## 1. Description / 概要 / 簡介

### [English]
This API automatically analyzes your uploaded images using advanced AI and generates highly optimized titles and 50 SEO keywords specifically tailored for the **Adobe Stock** search algorithm. It helps creators drastically reduce the time spent on manual tagging.

### [日本語]
このAPIは、アップロードされた画像を高度なAIで解析し、**Adobe Stock**の検索アルゴリズムに最適化された「タイトル」と「50個のSEOキーワード」を自動生成します。タグ付けの手間を大幅に削減し、クリエイターの作業を効率化します。

### [繁體中文]
此 API 使用先進的 AI 技術自動分析您上傳的圖片，並生成專為 **Adobe Stock** 搜尋演算法優化的「標題」與「50 個 SEO 關鍵字」。大幅減少創作者手動標記標籤的時間，提升上傳效率。

---

## 2. Key Features / 特徴 / 主要功能

### [English]
* **High Precision:** Tailored prompt constraints guarantee exactly 50 relevant keywords and a descriptive title based on image content.
* **Cost Protection:** Strictly limited to 1 image per request with validation to prevent accidental bulk-billing.
* **Ready-to-Use Output:** Returns a clean JSON object containing `Filename`, `Title`, and a comma-separated `Keywords` string perfectly formatted for Adobe Stock.

### [日本語]
* **高い精度:** 画像内容に基づき、正確なタイトルと厳密に50個の関連キーワードを生成します。
* **コスト防御:** 1回のリクエストにつき画像1枚に制限するバリデーションを搭載し、不正な大量課金を防ぎます。
* **即時利用可能な出力:** `Filename`、`Title`、およびカンマ区切りの `Keywords` 文字列を含むクリーンなJSONオブジェクトを返し、そのままAdobe Stockのメタデータとして活用できます。

### [繁體中文]
* **高精確度:** 根據圖片內容，生成精確的標題與嚴格限制在 50 個的相關關鍵字。
* **成本防護:** 限制每次請求僅能處理 1 張圖片，具備嚴格驗證機制以防止異常的大量計費。
* **即開即用格式:** 返回包含 `Filename`、`Title` 以及以逗號分隔的 `Keywords` 字串的乾淨 JSON 物件，完全符合 Adobe Stock 的上傳規範。

---

## 3. How to Generate Adobe Stock CSV (Python Example)
## CSV出力用Pythonコード（共通） / 批量生成 CSV 用的 Python 範例程式碼

### [English]
Since this API processes one image per request, you can use the following Python script to loop through an entire local folder, call the API for each image, and seamlessly compile all results into a single consolidated CSV file ready for direct upload to Adobe Stock.

### [日本語]
このAPIは1リクエストにつき1枚の画像を処理する仕様ですが、以下のPythonスクリプトを使用することで、ローカルフォルダ内のすべての画像を自動でループ処理し、最終的にAdobe Stockにそのままアップロードできる1本のCSVファイルへと綺麗にまとめ上げることができます。

### [繁體中文]
雖然此 API 每次請求僅處理 1 張圖片，但透過下方提供的 Python 腳本，您可以自動循環處理本地資料夾內的所有圖片，並將所有解析結果完美整合至單一 CSV 檔案中，直接上傳至 Adobe Stock 後台。

```python
import os
import csv
import requests

# ==========================================
#  Configuration / 設定 / 設定
# ==========================================
API_URL = "YOUR_RAPIDAPI_ENDPOINT_URL"  # e.g., [https://your-api.p.rapidapi.com/analyze-image](https://your-api.p.rapidapi.com/analyze-image)
API_KEY = "YOUR_RAPIDAPI_KEY"           # Your personal RapidAPI Key
IMAGE_DIR = "./my_stock_images"         # Folder containing your source images (.jpg, .png)
CSV_FILE = "adobe_stock_upload.csv"     # Output consolidated CSV path

headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "YOUR_RAPIDAPI_HOST_NAME"  # E.g., adobe-stock-metadata.p.rapidapi.com
}

def main():
    if not os.path.exists(IMAGE_DIR):
        print(f"Error: Folder '{IMAGE_DIR}' not found. Please create it first.")
        return

    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Filename", "Title", "Keywords"])

    print(f"Starting processing loop. Results will be saved to '{CSV_FILE}'...")

    for filename in os.listdir(IMAGE_DIR):
        if filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            file_path = os.path.join(IMAGE_DIR, filename)
            
            print(f"Processing: {filename}")
            
            with open(file_path, "rb") as img_file:
                files = {"file": (filename, img_file, "image/jpeg")}
                
                try:
                    response = requests.post(API_URL, headers=headers, files=files)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as file:
                            writer = csv.writer(file)
                            writer.writerow([
                                data.get("Filename", filename),
                                data.get("Title", ""),
                                data.get("Keywords", "")
                            ])
                        print(f" -> [Success] Metadata appended safely.")
                    else:
                        print(f" -> [Error {response.status_code}] {response.text}")
                        
                except Exception as e:
                    print(f" -> [Exception] Failed to process request: {e}")

    print("\n==================================================")
    print(f"Execution Completed! Your consolidated CSV is ready.")
    print(f"Path: {os.path.abspath(CSV_FILE)}")
    print("==================================================")

if __name__ == "__main__":
    main()
