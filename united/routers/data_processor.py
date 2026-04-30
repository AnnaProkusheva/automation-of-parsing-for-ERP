from fastapi import APIRouter, UploadFile, File, HTTPException, Form
import pandas as pd, io, re, json
from config import logger

router = APIRouter(prefix="/api/data", tags=["Обработка данных"])

@router.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents)).fillna("")
        return {"status": "success", "data": df.to_dict(orient="records")}
    except Exception as e:
        logger.error(f"Upload error: {e}"); raise HTTPException(400, f"Ошибка загрузки: {str(e)}")

@router.post("/normalize")
async def normalize_data(data: str = Form(...), rules_file: UploadFile = File(None)):
    try:
        data_list = json.loads(data); df = pd.DataFrame(data_list)
        rules = {}
        if rules_file and rules_file.filename:
            rules_content = await rules_file.read()
            if rules_file.filename.endswith(('.xlsx', '.xls')):
                rules_df = pd.read_excel(io.BytesIO(rules_content))
                rules = dict(zip(rules_df.iloc[:, 0].astype(str), rules_df.iloc[:, 1].astype(str)))
            else:
                rules_content = rules_content.decode('utf-8', errors='ignore')
                for line in rules_content.strip().split('\n'):
                    if ',' in line: k, v = line.split(',', 1); rules[k.strip()] = v.strip()
        clean_rules = {re.sub(r'[\s\.\,\-\_]+', '', str(k)).lower(): str(v) for k, v in rules.items()}
        src_col = next((c for c in df.columns if 'модель' in c.lower() and 'после' not in c.lower()), None)
        if not src_col: raise HTTPException(400, "Колонка 'Модель' не найдена")
        def smart_norm(x):
            if pd.isna(x): return x
            key = re.sub(r'[\s\.\,\-\_]+', '', str(x)).lower()
            return clean_rules.get(key, next((v for rk, v in clean_rules.items() if rk in key), x))
        df["Модель после нормализации"] = df[src_col].apply(smart_norm)
        return {"status": "success", "data": df.to_dict(orient="records")}
    except json.JSONDecodeError: raise HTTPException(400, "Неверный формат данных")
    except Exception as e:
        logger.error(f"Normalize error: {e}", exc_info=True); raise HTTPException(500, f"Ошибка: {str(e)[:200]}")

@router.post("/classify")
async def classify_data(data: str = Form(...), classifier_file: UploadFile = File(None)):
    try:
        data_list = json.loads(data); df = pd.DataFrame(data_list)
        class_map = {}
        if classifier_file and classifier_file.filename:
            clf_content = await classifier_file.read()
            if classifier_file.filename.endswith(('.xlsx', '.xls')):
                clf_df = pd.read_excel(io.BytesIO(clf_content))
                for _, row in clf_df.iterrows():
                    if pd.notna(row.get('Модель')):
                        key = str(row['Модель']).strip().lower()
                        class_map[key] = {'Класс': row.get('Класс',''), 'Подкласс': row.get('Подкласс','')}
        target = next((c for c in ["Модель после нормализации", "Модель"] if c in df.columns), None)
        if not target: raise HTTPException(400, "Нет колонки 'Модель'")
        def apply_cls(x):
            if pd.isna(x): return None, None
            m = class_map.get(str(x).strip().lower()); return (m['Класс'], m['Подкласс']) if m else (None, None)
        df[["Класс", "Подкласс"]] = df[target].apply(lambda x: pd.Series(apply_cls(x)))
        return {"status": "success", "data": df.to_dict(orient="records")}
    except Exception as e:
        logger.error(f"Classify error: {e}", exc_info=True); raise HTTPException(500, f"Ошибка: {str(e)[:200]}")