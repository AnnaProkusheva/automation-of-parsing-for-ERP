# config.py
import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
SETTINGS_FILE = DATA_DIR / "settings.json"

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(DATA_DIR / "app.log", encoding="utf-8", mode="a"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("unified_app")

# Настройки с приоритетом .env
DEFAULT_SETTINGS = {
    "provider": "openrouter",
    "api_key": (
        os.getenv("OPENROUTER_API_KEY") or
        os.getenv("YANDEX_GPT_API_KEY") or
        os.getenv("GIGACHAT_API_KEY") or
        os.getenv("OPENAI_API_KEY") or
        ""
    ),
    "model": "openai/gpt-4o-2024-08-06",  # ✅ Рабочая дефолтная модель
    "max_tokens": int(os.getenv("DEFAULT_MAX_TOKENS", "3000")),
    "master_prompt": """Ты инженер, специалист по формированию технологических карт и работ по ТОиР оборудования.
{file_instruction}
Необходимо заполнить:
Столбец "Элемент" — основной крупный элемент, входящий в состав узла. Например: Система смазки.
Столбец "Подэлемент" — более мелкий элемент, входящий в состав элемента. Например: Картер.
Правила:
• Каждый новый узел, элемент и подэлемент — в отдельной строке по порядку.
• НЕ вноси как "Элемент" или "Подэлемент": гайки, шайбы, винты, шпильки, хомуты, болты, штифты, шпонки.
• Если в столбцах несколько слов — первое слово всегда существительное, остальные после него.
• Элемент и подэлемент — в единственном числе, именительном падеже.
• Слова нельзя сокращать и заменять синонимами.
• Другие столбцы таблицы не удаляй и не изменяй.
ОТВЕТ ДОЛЖЕН БЫТЬ В СТРОГОМ ФОРМАТЕ:
[ТЕКСТ_ОТВЕТ]
Краткое текстовое описание результата для пользователя.
[/ТЕКСТ_ОТВЕТ]
[ТАБЛИЦА]
Элемент|Подэлемент|Наименование операции|Краткое содержание работ|Вид ТОиР|Периодичность|Норма времени, часов|Количество исполнителей|Профессия/Квалификация|Трудоёмкость, человеко/часов|Наименование ТМЦ|Количество ТМЦ|Единицы измерения ТМЦ|Наименование инструменты|Средства индивидуальной защиты|Требования по безопасности
Система смазки|Картер|Осмотр|Визуальный осмотр картера на наличие трещин и подтёков|ТО-1|4320|2.0|1|Слесарь по ремонту автомобилей, 3 разряд|2.0|||||Каска защитная, 1 шт; Очки защитные, 1 шт; Перчатки защитные, 1 пара|Затормозить технику; Выполнять работы при неработающем двигателе
[/ТАБЛИЦА]
ВАЖНО: Каждая строка таблицы — значения через "|". Всего 16 столбцов. Если данных нет — оставьте пусто (||)."""
}


def load_settings() -> dict:
    settings = {
        "provider": os.getenv("AI_PROVIDER", "openrouter"),
        "api_key": (
            os.getenv("OPENROUTER_API_KEY") or
            os.getenv("YANDEX_GPT_API_KEY") or
            os.getenv("GIGACHAT_API_KEY") or
            os.getenv("OPENAI_API_KEY") or
            ""
        ),
        "model": os.getenv("LLM_MODEL", "anthropic/claude-3-5-sonnet-20240620"),
        "max_tokens": int(os.getenv("DEFAULT_MAX_TOKENS", "3000")),
        "master_prompt": DEFAULT_SETTINGS["master_prompt"]
    }
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                for key in ["model", "max_tokens", "master_prompt"]:
                    if key in saved and not os.getenv(f"DEFAULT_{key.upper()}" if key != "master_prompt" else "MASTER_PROMPT"):
                        settings[key] = saved[key]
        except Exception as e:
            logger.warning(f"Ошибка чтения settings.json: {e}")
    return settings


def save_settings(settings: dict) -> bool:
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            # 👇 Ключевое: ensure_ascii=False
            json.dump(settings, f, ensure_ascii=False, indent=2)
        logger.info("Настройки сохранены")
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
        return False