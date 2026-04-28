import requests
import re
import time
from typing import List, Dict, Optional, Set
from bs4 import BeautifulSoup


class ElcomParser:
    """Парсер prm.elcomspb.ru с обходом ограничений каталога"""

    BASE_URL = "https://prm.elcomspb.ru"
    SEARCH_URL = f"{BASE_URL}/search/"
    CATALOG_URL = f"{BASE_URL}/retail/pumps/"

    # Паттерны
    ARTICLE_PATTERN = re.compile(r'02\.\d{2}\.\d{6}')
    MODEL_KEYWORDS = ['насос', 'гном', 'эцв', 'к\\s*\\d+', '1[кд]\\s*\\d+', '2д\\s*\\d+']

    def __init__(self, delay: float = 1.5, timeout: int = 30):
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'ru-RU,ru;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

    @staticmethod
    def clean(text: str) -> str:
        return re.sub(r'\s+', ' ', text.strip())

    def _extract_specs_from_title(self, title: str) -> Dict[str, Optional[str]]:
        """Извлечение характеристик из названия товара"""
        specs = {'flow_rate': None, 'head': None, 'motor_power': None, 'rotation_speed': None}

        # Паттерн: "7.5/3000" → мощность/обороты
        match = re.search(r'(\d+[\.,]?\d*)\s*[/,]\s*(\d{3,4})(?:\s*(?:кВт|без|на))?', title)
        if match:
            specs['motor_power'] = match.group(1).replace(',', '.')
            specs['rotation_speed'] = match.group(2)

        # Паттерн: "под 7.5 кВт"
        match = re.search(r'под\s*(\d+[\.,]?\d*)\s*кВт', title, re.IGNORECASE)
        if match and not specs['motor_power']:
            specs['motor_power'] = match.group(1).replace(',', '.')

        # ГНОМ: "ГНОМ 7-7-32/0,37-220"
        match = re.search(r'ГНОМ\s+(\d+)[\-\s]+(\d+)[\-\s]+[\d/]+/([\d,]+)', title)
        if match:
            specs['flow_rate'] = match.group(1)
            specs['head'] = match.group(2)
            specs['motor_power'] = match.group(3).replace(',', '.')

        return specs

    def _extract_model_from_title(self, title: str) -> str:
        """Извлечение чистой модели из названия"""
        # Убираем "Насос" в начале
        title = re.sub(r'^насос\s+', '', title, flags=re.IGNORECASE)

        # Берём часть до служебных слов
        stop_words = r'\s+(?:с|под|без|на|эл\.?дв\.?|квт|рамы|сд|с\s+эл\.?дв\.?)\b'
        model = re.split(stop_words, title, flags=re.IGNORECASE)[0].strip()

        # Очищаем от лишних символов
        model = re.sub(r'\s+', ' ', model).strip()
        return model if model else title.split()[0] if title.split() else title

    def _parse_catalog_item(self, text_block: str) -> Optional[Dict]:
        """Парсинг одного товара из текстового блока каталога"""
        lines = [self.clean(l) for l in text_block.split('\n') if self.clean(l)]

        # Поиск артикула
        article = None
        title = None
        for line in lines:
            if self.ARTICLE_PATTERN.match(line):
                article = line
                break

        if not article:
            return None

        # Поиск названия (строка, начинающаяся с "Насос")
        for line in lines:
            if line.lower().startswith('насос'):
                title = line
                break

        if not title:
            return None

        specs = self._extract_specs_from_title(title)
        model = self._extract_model_from_title(title)

        return {
            'model': model,
            'flow_rate': specs['flow_rate'],
            'head': specs['head'],
            'motor_power': specs['motor_power'],
            'rotation_speed': specs['rotation_speed'],
            'url': None,  # Будет заполнено позже
            'article': article,
            '_title': title  # Временное поле для отладки
        }

    def _extract_catalog_items(self, html: str) -> List[Dict]:
        """Извлечение всех товаров из HTML каталога"""
        soup = BeautifulSoup(html, 'html.parser')

        # Удаляем лишние элементы
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', '.breadcrumbs']):
            tag.decompose()

        # Получаем текст и разбиваем на блоки по артикулам
        text = soup.get_text(separator='\n', strip=True)
        lines = text.split('\n')

        items = []
        current_block = []

        for line in lines:
            line = self.clean(line)
            if not line:
                continue

            # Если нашли артикул — начинаем новый блок
            if self.ARTICLE_PATTERN.match(line):
                if current_block:
                    item = self._parse_catalog_item('\n'.join(current_block))
                    if item:
                        items.append(item)
                current_block = [line]
            else:
                current_block.append(line)

        # Последний блок
        if current_block:
            item = self._parse_catalog_item('\n'.join(current_block))
            if item:
                items.append(item)

        return items

    def _search_product_url(self, article: str) -> Optional[str]:
        """Поиск URL детальной страницы товара через поиск сайта"""
        try:
            # Поиск по артикулу
            search_url = f"{self.SEARCH_URL}?q={article}"
            response = self.session.get(search_url, timeout=self.timeout)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            # Ищем первую ссылку на товар с этим артикулом
            for link in soup.select('a[href*="/retail/"]'):
                href = link.get('href', '')
                if article in href and '/retail/pumps/' in href:
                    return self.BASE_URL + href if href.startswith('/') else href

            return None
        except Exception:
            return None

    def _parse_detail_page(self, url: str) -> Optional[Dict[str, str]]:
        """Парсинг детальной страницы для извлечения характеристик"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            specs = {}

            # Поиск таблицы характеристик
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = self.clean(cells[0].get_text()).lower()
                        value = self.clean(cells[1].get_text())

                        # Извлечение числовых значений
                        if any(kw in label for kw in ['подача', 'расход', 'производительность']):
                            match = re.search(r'([\d,\.]+)', value)
                            if match:
                                specs['flow_rate'] = match.group(1).replace(',', '.')
                        elif any(kw in label for kw in ['напор', 'высота']):
                            match = re.search(r'([\d,\.]+)', value)
                            if match:
                                specs['head'] = match.group(1).replace(',', '.')
                        elif 'мощность' in label and 'квт' in label:
                            match = re.search(r'([\d,\.]+)', value)
                            if match:
                                specs['motor_power'] = match.group(1).replace(',', '.')
                        elif any(kw in label for kw in ['об/мин', 'оборот', 'частота']):
                            match = re.search(r'(\d{3,4})', value)
                            if match:
                                specs['rotation_speed'] = match.group(1)

            return specs if any(specs.values()) else None
        except Exception:
            return None

    def _normalize_query(self, query: str) -> str:
        """Нормализация поискового запроса для лучшего совпадения"""
        # Приводим к нижнему регистру, убираем лишние пробелы
        query = query.lower().strip()
        # Заменяем "к" на "к" без пробелов для моделей типа "1К 80"
        query = re.sub(r'(\d)\s*([ккмд])\s*(\d)', r'\1\2\3', query, flags=re.IGNORECASE)
        return query

    def _matches_query(self, model: str, query: str) -> bool:
        """Проверка, соответствует ли модель поисковому запросу"""
        model_norm = self._normalize_query(model)
        query_norm = self._normalize_query(query)

        # Прямое вхождение
        if query_norm in model_norm:
            return True

        # Поиск по ключевым словам с цифрами
        # Например: "1 к 80" → ищем "1к80" или "к 80"
        parts = query_norm.split()
        if len(parts) >= 2:
            # Комбинации: "1к", "к80", "1к80"
            combined = ''.join(parts)
            if combined in model_norm:
                return True
            # Отдельные части
            for part in parts:
                if part in model_norm and len(part) > 1:
                    return True

        # Regex-поиск для моделей типа "К 65", "1К 80"
        pattern = re.sub(r'\s+', r'\\s*', re.escape(query_norm))
        if re.search(pattern, model_norm, re.IGNORECASE):
            return True

        return False

    def search(self, model_query: str, max_pages: int = 30, fetch_details: bool = False) -> List[Dict]:
        """
        Поиск насосов по модели

        :param model_query: Запрос пользователя
        :param max_pages: Максимум страниц каталога для проверки
        :param fetch_details: Если True — парсить детальные страницы для характеристик (медленно!)
        """
        all_items = []
        seen_articles: Set[str] = set()

        print(f"🔍 Поиск '{model_query}' на prm.elcomspb.ru...")

        try:
            for page in range(1, max_pages + 1):
                url = self.CATALOG_URL if page == 1 else f"{self.CATALOG_URL}?PAGEN_1={page}"

                response = self.session.get(url, timeout=self.timeout)
                if response.status_code != 200:
                    break

                response.encoding = 'utf-8'
                items = self._extract_catalog_items(response.text)

                if not items:
                    if page == 1:
                        print(f"  ⚠️  Не найдено товаров")
                    break

                print(f"  Страница {page}: {len(items)} товаров")

                # Фильтрация по модели
                for item in items:
                    if item['article'] in seen_articles:
                        continue

                    if self._matches_query(item['model'], model_query):
                        seen_articles.add(item['article'])

                        # Если нужно — получаем характеристики с детальной страницы
                        if fetch_details:
                            print(f"    🔗 Поиск страницы для {item['article']}...")
                            detail_url = self._search_product_url(item['article'])
                            if detail_url:
                                item['url'] = detail_url
                                specs = self._parse_detail_page(detail_url)
                                if specs:
                                    # Обновляем только пустые поля
                                    for key, value in specs.items():
                                        if value and not item.get(key):
                                            item[key] = value
                                time.sleep(self.delay * 0.5)
                            time.sleep(self.delay * 0.3)

                        # Удаляем временное поле
                        item.pop('_title', None)
                        all_items.append(item)

                # Проверка: есть ли следующая страница?
                if f'> {page + 1}<' not in response.text and f'PAGEN_1={page + 1}' not in response.text:
                    break

                time.sleep(self.delay)

        except Exception as e:
            print(f"  ⚠️  Ошибка: {e}")

        print(f"✅ Найдено: {len(all_items)} насосов")
        return all_items