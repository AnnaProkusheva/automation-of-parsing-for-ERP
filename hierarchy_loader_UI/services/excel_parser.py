import pandas as pd
import json

def build_smart_hierarchy(df):
    """
    Строит иерархию из DataFrame.
    Игнорирует '*', '-', выполняет forward-fill.
    """
    df = df.fillna('').astype(str)
    
    if df.empty:
        return {'name': 'Пустой файл', 'children': [], 'model': ''}

    root = {'name': 'Северал', 'children': [], 'model': ''}
    num_levels = len(df.columns) - 1
    current_path = [''] * num_levels
    
    try:
        for index, row in df.iterrows():
            row_vals = row.tolist()
            raw_model = row_vals[-1].strip()
            
            if raw_model in ['*', '-']:
                model = ''
            else:
                model = raw_model

            hierarchy_vals = row_vals[:-1]
            actual_depth = 0
            
            for i in range(len(hierarchy_vals)):
                val = str(hierarchy_vals[i]).strip()
                if val in ['*', '-']:
                    val = ''
                
                if val:
                    current_path[i] = val
                    actual_depth = i + 1
            
            if actual_depth == 0 and not model:
                continue

            current_node_ref = root
            for i in range(actual_depth):
                level_name = current_path[i]
                found_child = None
                for child in current_node_ref['children']:
                    if child['name'] == level_name:
                        found_child = child
                        break
                
                if found_child:
                    if i == actual_depth - 1 and model:
                        found_child['model'] = model
                    current_node_ref = found_child
                else:
                    new_node = {
                        'name': level_name,
                        'children': [],
                        'model': model if (i == actual_depth - 1 and model) else ''
                    }
                    current_node_ref['children'].append(new_node)
                    current_node_ref = new_node
        return root
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА ПАРСЕРА: {e}")
        return {'name': 'Ошибка парсера', 'children': [], 'model': str(e)}

def flatten_hierarchy(node, path=[], result=None):
    if result is None: result = []
    new_path = path + [node['name']]
    result.append({
        'Путь': ' → '.join(new_path),
        'Модель': node.get('model', ''),
        'Уровень': len(new_path)
    })
    for child in node.get('children', []):
        flatten_hierarchy(child, new_path, result)
    return result