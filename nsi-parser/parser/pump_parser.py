import requests
from bs4 import BeautifulSoup
import re
import time
from typing import List, Dict, Optional


class PumpParser:
    BASE_URL = "https://nasoscentr.ru"
    CATALOG_URL = f"{BASE_URL}/catalog/nasosy-tipa-d-1d-2d/"

    def __init__(self, delay: float = 2.0, timeout: int = 30):
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'ru-RU,ru;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

    @staticmethod
    def clean_text(text: Optional[str]) -> str:
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip()).strip()

    def _parse_specs_from_text(self, text: str) -> Dict[str, str]:
        specs = {}
        text = re.sub(r'\s+', ' ', text)

        keywords = ['Подача', 'Расход', 'Напор', 'Мощность двигателя', 'Мощность', 'Частота вращения', 'Обороты']
        pattern = re.compile('(' + '|'.join(keywords) + ')', re.IGNORECASE)
        parts = pattern.split(text)

        for i in range(1, len(parts) - 1, 2):
            keyword = parts[i].lower()
            raw_val = parts[i + 1].split('.')[0].split('Подробнее')[0].split('В корзину')[0].split('насос')[0].strip()

            val = re.sub(r'[^0-9,\.\-]', ' ', raw_val).strip()
            val = re.sub(r'\s+', ', ', val).strip()
            val = re.sub(r',+', ',', val).strip(', ')

            if not val:
                continue

            if 'подач' in keyword or 'расход' in keyword:
                specs['flow_rate'] = val
            elif 'напор' in keyword:
                specs['head'] = val
            elif 'мощн' in keyword:
                specs['motor_power'] = val
            elif 'частот' in keyword or 'оборот' in keyword:
                specs['rotation_speed'] = val
        return specs

    def _extract_card(self, card) -> Optional[Dict]:
        model = None
        for tag in ['h3', 'h4', 'h5', 'a.name', 'a.title', '.item-title', '.catalog-item__name']:
            el = card.select_one(tag)
            if el and el.get_text(strip=True):
                model = el.get_text(strip=True)
                break
        if not model:
            return None

        specs = self._parse_specs_from_text(card.get_text())
        if not specs:
            return None

        link_el = card.select_one('a[href*="/catalog/"]')
        url = ""
        if link_el and link_el.get('href'):
            href = link_el['href']
            url = self.BASE_URL + href if href.startswith('/') else href

        return {
            'model': model,
            'flow_rate': specs.get('flow_rate'),
            'head': specs.get('head'),
            'motor_power': specs.get('motor_power'),
            'rotation_speed': specs.get('rotation_speed'),
            'url': url
        }

    def search(self, model_query: str, max_pages: int = 5) -> List[Dict]:
        all_pumps = []
        pattern = re.compile(model_query, re.IGNORECASE)

        for page in range(1, max_pages + 1):
            url = self.CATALOG_URL if page == 1 else f"{self.CATALOG_URL}?PAGEN_1={page}"
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')

                cards = []
                for sel in ['.catalog-item', '.product-tile', '.goods-item', '.item', '.card', '.product-item']:
                    found = soup.select(sel)
                    if found:
                        cards = found
                        break

                if not cards:
                    for elem in soup.find_all(string=lambda t: t and ('Подача' in t or 'м³/ч' in t or 'м3/ч' in t)):
                        parent = elem.find_parent(['div', 'article', 'li', 'td'])
                        for _ in range(4):
                            if parent and (parent.get('data-product-id') or len(parent.get('class', [])) > 0):
                                if parent not in cards:
                                    cards.append(parent)
                                break
                            if parent:
                                parent = parent.find_parent()

                for card in cards:
                    pump = self._extract_card(card)
                    if pump and pattern.search(pump['model']):
                        all_pumps.append(pump)

                time.sleep(self.delay)
                if not cards:
                    break
            except Exception as e:
                print(f"Ошибка загрузки страницы {page}: {e}")
                break

        seen = set()
        unique = []
        for p in all_pumps:
            key = p['model'].lower()
            if key not in seen:
                seen.add(key)
                unique.append(p)
        return unique