# services/ai_service.py
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from openai import OpenAI
import config
from io import BytesIO
import pypdf # Библиотека для PDF

# Инициализация клиента OpenAI
client = OpenAI(
    base_url=config.AI_BASE_URL,
    api_key=config.AI_API_KEY
)

def search_real_links(query):
    """
    Возвращается к DuckDuckGo, так как Google заблокирован.
    """
    try:
        ddgs = DDGS(timeout=10)
        results = []
        
        # --- УМНАЯ СТРАТЕГИЯ ЗАПРОСА ---
        # 1. Тип файла PDF (это важно!)
        # 2. Исключаем слова покупки
        smart_query = f"{query} filetype:pdf -купить -цена -магазин"
        
        print(f"Поиск DDG: {smart_query}")
        
        search_results = ddgs.text(smart_query, max_results=5)
        
        for result in search_results:
            title = result.get("title", "")
            url = result.get("href")
            snippet = result.get("body", "")[:120]
            
            # Дополнительный фильтр на стороне клиента:
            # Если в заголовке есть слова "Купить" или "Price" — пропускаем
            if any(word in title.lower() for word in ["купить", "price", "цена", "shop"]):
                continue
            
            results.append({
                "title": title,
                "url": url,
                "snippet": snippet + "..."
            })
            
        if not results:
            return [{"error": "Поиск не дал результатов (только магазины?). Попробуйте вставить ссылку вручную."}]
            
        return results
        
    except Exception as e:
        print(f"Ошибка DDG: {e}")
        return [{"error": f"Поиск временно недоступен. Используйте поле 'Вставить ссылку' ниже."}]

def parse_and_analyze(url, model_name):
    """
    Универсальный анализатор с максимальной защитой от падений.
    """
    text_content = ""
    source_info = url

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code != 200:
            return {"error": f"Ошибка доступа (код {response.status_code})"}

        content_type = response.headers.get('Content-Type', '').lower()
        print(f"Тип файла: {content_type}")

        # --- ЛОГИКА PDF ---
        if 'application/pdf' in content_type:
            print("Обнаружен PDF. Извлекаю текст...")
            try:
                # Проверка: установлен ли pypdf
                import pypdf
            except ImportError:
                return {"error": "Библиотека pypdf не установлена. Выполните в терминале: pip install pypdf"}

            try:
                pdf_reader = pypdf.PdfReader(BytesIO(response.content))
                if pdf_reader.is_encrypted:
                    try:
                        pdf_reader.decrypt('')
                    except:
                        return {"error": "PDF-файл защищен паролем."}
                
                text_content = ""
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + " "
                
                text_content = text_content.replace('\n', ' ').strip()
                print(f"Извлечено текста: {len(text_content)} символов")
                
                if len(text_content) < 100:
                    return {"error": "PDF-файл пуст или содержит только картинки."}
                    
            except Exception as pdf_err:
                return {"error": f"Ошибка чтения PDF: {str(pdf_err)}"}

        # --- ЛОГИКА HTML ---
        else:
            soup = BeautifulSoup(response.content, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.extract()
            text_content = soup.get_text(separator=' ', strip=True)
            
            if len(text_content) < 200:
                return {"error": "На странице недостаточно текста."}

    except Exception as e:
        print(f"Ошибка этапа 1 (Скачивание): {e}")
        return {"error": f"Не удалось скачать страницу: {str(e)}"}

    # --- ЭТАП 2: АНАЛИЗ ---
    try:
        if not text_content:
            return {"error": "Нет текста для анализа."}

        text_sample = text_content[:3500]
        
        prompt = f"""
        Проанализируй текст технической документации для модели {model_name}.
        
        Текст страницы:
        \"{text_sample}\"
        
        Задача: Найди и выпиши точные технические характеристики.
        Если характеристик нет (это каталог, цены), напиши строго: "Характеристики не найдены".
        Если характеристики есть, выведи их списком:
        - Параметр: значение
        """

        completion = client.chat.completions.create(
            model=config.AI_MODEL_ID,
            messages=[
                {"role": "system", "content": "Ты анализатор документации."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return {"analysis": completion.choices[0].message.content, "url": url}
        
    except Exception as e:
        print(f"Ошибка этапа 2 (ИИ): {e}")
        return {"error": f"Ошибка ИИ: {str(e)}"}