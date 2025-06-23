from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.database.database import engine
from app.models import models
from app.routers import problems, submissions

# データベーステーブルの作成
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Python課題アドバイス生成システム",
    description="GCI講座用のPython課題自動アドバイス生成API",
    version="1.0.0"
)

# 静的ファイルとテンプレートの設定
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# APIルーターの登録
app.include_router(problems.router, prefix="/api")
app.include_router(submissions.router, prefix="/api")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    メインページ
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """
    管理者ページ
    """
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/health")
async def health_check():
    """
    ヘルスチェック
    """
    return {"status": "healthy", "message": "Python課題アドバイス生成システム"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)