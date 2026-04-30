# 🛠 Unified Engineering Portal

## 📋 О проекте

**Unified Engineering Portal** — это веб-приложение для инженеров и специалистов по ТОиР, которое автоматизирует:

| Функция | Описание |
|---------|----------|
| 🔍 **Поиск насосов** | Парсинг каталогов [nasoscentr.ru](https://nasoscentr.ru) и [prm.elcomspb.ru](https://prm.elcomspb.ru) по модели оборудования |
| 🤖 **Генерация ТК** | Создание технологических карт через ИИ (OpenRouter, OpenAI) с загрузкой техпаспортов |
| 📥 **Экспорт** | Выгрузка результатов в Excel (.xlsx) или JSON |

## 🚀 Быстрый старт

### 1️⃣ Клонирование репозитория

```bash
git clone https://github.com/AnnaProkusheva/automation-of-parsing-for-ERP.git
cd automation-of-parsing-for-ERP/united
```

### 2️⃣ Создание виртуального окружения

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate  # Windows
```

### 3️⃣ Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4️⃣ Настройка окружения

Создайте файл `.env` в корне проекта:

```env
# 🔑 API ключ (выберите один провайдер)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxx

# 🌐 Сервер
APP_HOST=0.0.0.0
APP_PORT=8000
RELOAD=true

# 🤖 AI (опционально, дефолты в коде)
AI_PROVIDER=openrouter
LLM_MODEL=openai/gpt-4o-2024-08-06
DEFAULT_MAX_TOKENS=3000
DEFAULT_TEMPERATURE=0.3

# ⏱ Запросы
REQUEST_TIMEOUT=120
REQUEST_DELAY=2.0
MAX_RETRIES=3
```

> 💡 **Минимальный `.env`** — только ключ:
> ```env
> OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxx
> ```
> Все остальные настройки имеют значения по умолчанию.

### 5️⃣ Запуск сервера

```bash
uvicorn main:app --reload
```

Приложение доступно по адресу: **http://localhost:8000**

📚 Swagger-документация: **http://localhost:8000/docs**

---

## 🗂 Структура проекта

```
united/
├── main.py                    # Точка входа FastAPI
├── config.py                  # Настройки, загрузка .env, логирование
├── requirements.txt           # Зависимости Python
├── .env                       # Переменные окружения (не коммитить!)
├── .gitignore                 # Исключения для Git
│
├── routers/                   # API-роутеры
│   ├── __init__.py
│   ├── pumps.py              # Поиск и экспорт насосов
│   ├── ai_generator.py       # Генерация ТК через ИИ
│   └── data_processor.py     # Загрузка/нормализация/классификация
│
├── core/                      # Бизнес-логика
│   ├── __init__.py
│   ├── pump_parser.py        # Парсер nasoscentr.ru
│   └── elcom_parser.py       # Парсер prm.elcomspb.ru
│
├── templates/                 # Frontend
│   └── index.html            # Единый веб-интерфейс
│
└── data/                      # Данные (создаётся автоматически)
    ├── settings.json         # Пользовательские настройки ИИ
    └── app.log               # Логи приложения
```

---

## 🎯 Использование

### 🔍 Поиск насосов

1. Откройте вкладку **"🔍 Насосы"**
2. Введите модель (например, `Д 200`)
3. Укажите количество страниц для поиска (1–20)
4. Нажмите **"🔎 Искать"**
5. Результаты отобразятся в таблице с возможностью экспорта в Excel/JSON

### 🤖 Генерация технологической карты

1. Перейдите на вкладку **"🤖 ТК (ИИ)"**
2. Заполните:
   - **Модель оборудования**: `Д 160-112а`
   - **Класс**: `Насосы`
   - **Подкласс**: `Центробежные` (опционально)
   - **Запрос**: дополнительная инструкция для ИИ
3. (Опционально) Прикрепите техпаспорт: **PDF / DOCX / TXT**
4. Выберите модель ИИ из выпадающего списка
5. Нажмите **"🤖 Сгенерировать ТК"**
6. Скачайте результат в формате **.xlsx**

#### ✅ Поддерживаемые модели ИИ

| Провайдер | Модель | Статус |
|-----------|--------|--------|
| OpenAI | `openai/gpt-4o-2024-08-06` | ✅ |
| OpenAI | `openai/gpt-4o-mini` | ✅ |
| Meta | `meta-llama/llama-3.3-70b-instruct` | ✅ |
| Mistral | `mistralai/mistral-large-2411` | ✅ |
| Z.AI | `z-ai/glm-4.5-air:free` | 🆓 |
| InclusionAI | `inclusionai/ling-2.6-1t:free` | 🆓 |
| OpenRouter | `openrouter/free` | 🆓 |

> ⚠️ Модели могут менять статус. Актуальный список: [openrouter.ai/models](https://openrouter.ai/models)

### ⚙️ Настройки ИИ

1. Откройте вкладку **"⚙️ Настройки"**
2. Выберите провайдера: OpenRouter / OpenAI / YandexGPT / GigaChat
3. Введите API-ключ (если не указан в `.env`)
4. Выберите модель и укажите `max_tokens`
5. Нажмите **"💾 Сохранить"**

Настройки сохраняются в `data/settings.json` и применяются ко всем запросам.

## 🔌 API Endpoints

### 🤖 Генерация ТК (`/api/ai/*`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `GET` | `/api/ai/settings` | Получить текущие настройки ИИ |
| `POST` | `/api/ai/settings` | Обновить настройки ИИ |
| `POST` | `/api/ai/chat` | Сгенерировать ТК (multipart/form-data) |
| `GET` | `/api/ai/table_template` | Получить шаблон заголовков таблицы |

**Пример запроса к `/api/ai/chat`:**

```bash
curl -X POST http://localhost:8000/api/ai/chat \
  -F "message=Сгенерируй ТК" \
  -F "model_name=1К80-50-200" \
  -F "equipment_class=Насосы" \
  -F "subclass=Центробежные" \
  -F "model=openai/gpt-4o-2024-08-06" \
  -F "file=@/path/to/manual.pdf"
```

### 🔍 Поиск насосов (`/api/pumps/*`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `POST` | `/api/pumps/search` | Поиск насосов по модели (JSON) |
| `POST` | `/api/pumps/export` | Экспорт результатов в Excel/JSON |

**Пример запроса к `/api/pumps/search`:**

```bash
curl -X POST http://localhost:8000/api/pumps/search \
  -H "Content-Type: application/json" \
  -d '{"model": "1К80", "pages": 5}'
```

## 🛠 Разработка

### Добавление нового роутера

1. Создайте файл в `routers/`, например `routers/reports.py`:
```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/reports", tags=["Отчёты"])

@router.get("/summary")
async def get_summary():
    return {"status": "ok"}
```

2. Подключите в `main.py`:
```python
from routers import reports
app.include_router(reports.router)
```

### Логирование

Логи пишутся в:
- Консоль (stdout)
- Файл: `data/app.log`

Уровни: `INFO`, `WARNING`, `ERROR`

Пример:
```python
from config import logger

logger.info("🔍 Поиск: '1К80'")
logger.error(f"Ошибка: {e}", exc_info=True)
```

---

## 🐳 Docker (опционально)

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Запуск

```bash
docker build -t unified-portal .
docker run -p 8000:8000 --env-file .env unified-portal
```

---

## ❓ Устранение неполадок

| Проблема | Решение |
|----------|---------|
| `401 Unauthorized` | Проверьте `OPENROUTER_API_KEY` в `.env` или настройках |
| `404: model not found` | Используйте актуальный ID модели из [openrouter.ai/models](https://openrouter.ai/models) |
| `422 Unprocessable Entity` | Проверьте формат запроса (FormData для `/api/ai/chat`) |
| Файл не загружается | Убедитесь, что размер < 16 МБ и формат: `.pdf`, `.docx`, `.txt` |
| Красные подчёркивания в IDE | Создайте `__init__.py` в `routers/` и `core/`, настройте интерпретатор |

### Проверка окружения

```bash
# Проверка импортов
python -c "from core.pump_parser import PumpParser; print('OK')"

# Проверка настроек
curl -s http://localhost:8000/api/ai/settings | python -m json.tool

# Проверка логов
tail -f data/app.log
```

---

## 📬 Контакты

- **Автор**: [Anna Prokusheva](https://github.com/AnnaProkusheva)
- **Репозиторий**: [github.com/AnnaProkusheva/automation-of-parsing-for-ERP](https://github.com/AnnaProkusheva/automation-of-parsing-for-ERP)

---

> ⚙️ *Проект находится в активной разработке. Функционал может меняться.*
