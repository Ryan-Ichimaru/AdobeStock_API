import os
import io
import json
import base64
from typing import List
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Depends, Header
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from openai import OpenAI

# 1. 初期設定（.envから環境変数を読み込む）
load_dotenv()

app = FastAPI(title="Image Metadata API")

async def verify_rapidapi_secret(x_rapidapi_proxy_secret: str = Header(default=None)):
    """
    RapidAPIからのリクエストであることを検証する依存関数。
    環境変数 RAPIDAPI_PROXY_SECRET が設定されている場合、
    ヘッダーの X-RapidAPI-Proxy-Secret と一致するか厳格にチェックします。
    """
    expected_secret = os.environ.get("RAPIDAPI_PROXY_SECRET")
    if expected_secret:
        if x_rapidapi_proxy_secret != expected_secret:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing RapidAPI Proxy Secret"
            )

@app.post("/analyze-image", dependencies=[Depends(verify_rapidapi_secret)])
async def analyze_image(file: UploadFile = File(...)):
    # =========================================
    # 3. APIキーの安全な管理（セキュリティ）
    # =========================================
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI API key is not configured."
        )

    client = OpenAI(api_key=api_key)
    
    # =========================================
    # 2. 防御ロジック - 枚数制限
    # =========================================
    # FastAPIの File(...) により、ファイル未送信時は自動的に 422 エラーとなります。
    # 複数ファイルが送信された場合も1つだけを抽出して安全に処理します。
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exactly one image file is required."
        )
    
    # =========================================
    # 2. 防御ロジック - 形式制限
    # =========================================
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed."
        )
    
    # ファイル内容の読み込み
    contents = await file.read()
    
    # =========================================
    # 2. 防御ロジック - サイズ制限 (10MB)
    # =========================================
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image size must not exceed 10MB."
        )

    # =========================================
    # 1. & コアロジックの継承
    # =========================================
    try:
        from PIL import Image
        # 画像フォーマット等に異常がないかPillowで確認
        img = Image.open(io.BytesIO(contents))
        if img.mode != 'RGB': 
            img = img.convert('RGB')
            
        # 既存ロジック：最大1024pxにリサイズ
        if max(img.size) > 1024:
            img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format or unable to process the image."
        )
    
    # 既存ロジック：OpenAIへのプロンプト内容を完全維持
    prompt = """
        Analyze this image and provide:
        1. A catchy title (max 70 chars, no commas).
        2. Exactly 50 highly relevant SEO keywords (comma-separated).
        
        Rules:
        - Use these 8 perspectives: Subject, Background, Color, Emotion, Technique, Concept, Season, Use-case.
        - Output ONLY a JSON object: {"title": "...", "keywords": "k1, k2, ..."}
        """
        
    try:
        # 既存ロジック：使用モデル（gpt-4o-mini）を完全維持
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={ "type": "json_object" },
            messages=[{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}", "detail": "low"}}
            ]}]
        )
        
        data = json.loads(response.choices[0].message.content)
        
        # 既存ロジック：データ整形
        title = data.get('title', 'Untitled').replace(',', '')
        keywords = data.get('keywords', '')
        
        # 既存のCSV出力と同じ「Filename, Title, Keywords」の構成で返却
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "Filename": file.filename,
                "Title": title,
                "Keywords": keywords
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OpenAI API processing failed: {str(e)}"
        )
