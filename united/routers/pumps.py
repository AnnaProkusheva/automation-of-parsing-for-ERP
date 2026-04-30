import json
import openpyxl
import os
import tempfile

from config import logger
from core.pump_parser import PumpParser
from core.elcom_parser import ElcomParser
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/pumps", tags=["Поиск насосов"])

@router.post("/search")
async def search_pumps(payload: dict = Body(...)):
    model = payload.get("model", "").strip()
    if not model: raise HTTPException(400, "Модель не указана")
    delay = float(os.getenv("REQUEST_DELAY", "2.0")); timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
    logger.info(f"🔍 Поиск: '{model}'")
    parser = PumpParser(delay=delay, timeout=timeout)
    results = parser.search(model, max_pages=payload.get("pages", 5))
    if not results:
        logger.info("🔄 Переход на резервный источник...")
        elcom = ElcomParser(delay=delay * 0.75, timeout=timeout)
        results = elcom.search(model, max_pages=5, fetch_details=payload.get("details", False))
    return {"success": True, "count": len(results), "data": results}

@router.post("/export")
async def export_pumps(payload: dict = Body(...)):
    fmt = payload.get("format", "excel"); data = payload.get("data", [])
    if not data: raise HTTPException(400, "Нет данных для экспорта")
    ext = "xlsx" if fmt == "excel" else "json"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}", dir=tempfile.gettempdir())
    if fmt == "excel":
        wb = openpyxl.Workbook(); ws = wb.active; ws.append(list(data[0].keys()))
        for row in data: ws.append(list(row.values()))
        wb.save(tmp.name)
    else:
        with open(tmp.name, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)
    return FileResponse(path=tmp.name, media_type="application/octet-stream", filename=f"pumps_export.{ext}")