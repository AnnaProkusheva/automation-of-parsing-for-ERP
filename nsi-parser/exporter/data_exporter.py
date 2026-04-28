import pandas as pd
import json
import os
from typing import List, Dict
from datetime import datetime


class DataExporter:
    COL_NAMES = {
        'model': 'Модель насоса',
        'flow_rate': 'Подача, м3/ч',
        'head': 'Напор, м',
        'motor_power': 'Мощность двигателя, кВт',
        'rotation_speed': 'Частота вращения, об/мин',
        'url': 'Ссылка'
    }

    @staticmethod
    def to_excel(data: List[Dict], filepath: str) -> str:
        if not data:
            return filepath
        df = pd.DataFrame(data)
        df = df.rename(columns=DataExporter.COL_NAMES)
        ordered_cols = [v for v in DataExporter.COL_NAMES.values() if v in df.columns]
        df = df[ordered_cols]
        df.to_excel(filepath, index=False, engine='openpyxl')
        return filepath

    @staticmethod
    def to_json(data: List[Dict], filepath: str) -> str:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return filepath

    @staticmethod
    def generate_filename(extension: str, prefix: str = 'pumps') -> str:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{prefix}_{timestamp}.{extension}"
