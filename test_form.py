import asyncio
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.testclient import TestClient

app = FastAPI()

@app.post("/test")
async def test(request: Request, swagger_file: UploadFile = File(default=None, alias="file")):
    form = await request.form()
    from starlette.datastructures import UploadFile as StarletteUploadFile
    files = [v for k, v in form.multi_items() if isinstance(v, UploadFile)]
    star_files = [v for k, v in form.multi_items() if isinstance(v, StarletteUploadFile)]
    types = [type(v).__name__ for k, v in form.multi_items()]
    return {"count": len(files), "star_count": len(star_files), "types": types}

client = TestClient(app)
with open("test.txt", "w") as f:
    f.write("hello")

with open("test.txt", "rb") as f:
    response = client.post("/test", files={"file": f})
print(response.json())
