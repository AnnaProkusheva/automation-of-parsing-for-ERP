# main.py — ТОЛЬКО точка входа (модульная архитектура)
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

# Загружаем .env ПЕРЕД любыми импортами
load_dotenv()

app = FastAPI(
    title="Unified Engineering Portal",
    description="Парсинг насосов • Генерация ТК • Обработка данных",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === ПОДКЛЮЧАЕМ РОУТЕРЫ (вся логика — в отдельных файлах) ===
# Важно: если в роутере уже указан prefix при создании APIRouter(),
# то здесь prefix указывать НЕ НУЖНО
from routers import pumps, ai_generator, data_processor

app.include_router(pumps.router)        # prefix="/api/pumps" уже внутри pumps.py
app.include_router(ai_generator.router) # prefix="/api/ai" уже внутри ai_generator.py
app.include_router(data_processor.router) # prefix="/api/data" уже внутри data_processor.py

# === Статика и шаблоны ===
BASE_DIR = Path(__file__).resolve().parent
os.makedirs(BASE_DIR / "templates", exist_ok=True)
os.makedirs(BASE_DIR / "static", exist_ok=True)

templates = Jinja2Templates(directory=BASE_DIR / "templates")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# === Главная страница ===
@app.get("/", tags=["Root"])
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# === Health check ===
@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "service": "unified-engineering-portal"}

# === Запуск ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", "8000")),
        reload=os.getenv("RELOAD", "true").lower() == "true"
    )