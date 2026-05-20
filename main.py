import os
import io
import json
import base64
import secrets  # タイミング攻撃対策用に追加
from typing import List
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Depends, Header
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = FastAPI(title="Image Metadata API")

async def verify_rapidapi_secret(x_rapidapi_proxy_secret: str = Header(default=None)):
    """
    RapidAPIからのリクエストであることを厳格に検証。
    """
    expected_secret = os.environ.get("RAPIDAPI_PROXY_SECRET")
    
    # 【修正2】環境変数自体が設定されていない場合は即座にエラー（バイパス防止）
    if not expected_secret:
        print("CRITICAL ERROR: RAPIDAPI_PROXY_SECRET is not set in environment variables.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error."
        )
        
    # 【修正5】secrets.compare_digestを使用してタイミング攻撃を防止
    if not x_rapidapi_proxy_secret or not secrets.compare_digest(x_rapidapi_proxy_secret, expected_secret):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing RapidAPI Proxy Secret"
        )

@app.post("/analyze-image", dependencies=[Depends(verify_rapidapi_secret)])
async def analyze_image(file: UploadFile = File(...)):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI API key is not configured."
        )

    client = OpenAI(api_key=api_key)
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exactly one image file is required."
        )
    
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed."
        )
    
    # 【修正3】メモリ枯渇(OOM)防止: チャンクごとに読み込んでサイズ制限をかける
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    contents = b""
    while chunk := await file.read(1024 * 1024):  # 1MBずつ読み込み
        contents += chunk
        if len(contents) > MAX_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Image size must not exceed 10MB."
            )
    
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(contents))
        if img.mode != 'RGB': 
            img = img.convert('RGB')
            
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
    
    prompt = """
        Analyze this image and provide:
        1. A catchy title (max 70 chars, no commas).
        2. Exactly 50 highly relevant SEO keywords (comma-separated).
        
        Rules:
        - Use these 8 perspectives: Subject, Background, Color, Emotion, Technique, Concept, Season, Use-case.
        - Output ONLY a JSON object: {"title": "...", "keywords": "k1, k2, ..."}
        """
        
    try:
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
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "Filename": file.filename,
                "Title": title,
                "Keywords": keywords
            }
        )
        
    except Exception as e:
        # 【修正4】詳細なエラーはサーバー側にのみ記録し、ユーザーには汎用エラーを返す
        print(f"OpenAI API Error: {str(e)}") 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while analyzing the image."
        )