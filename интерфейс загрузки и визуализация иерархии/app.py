from flask import Flask, render_template, request, send_file, jsonify
import pandas as pd
import json
from io import BytesIO, StringIO
import traceback

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
cache = {}

def build_smart_hierarchy(df):
    """
    Строит иерархию. 
    ИСПРАВЛЕНО: Игнорирует символ '*', если он используется как плейсхолдер пустоты.
    """
    df = df.fillna('').astype(str)
    
    if df.empty:
        return {'name': 'Пустой файл', 'children': [], 'model': ''}

    root = {'name': 'Северал', 'children': [], 'model': ''}
    
    # Храним текущий путь
    # Количество колонок минус одна (последняя - модель)
    num_levels = len(df.columns) - 1
    current_path = [''] * num_levels
    
    try:
        for index, row in df.iterrows():
            row_vals = row.tolist()
            
            # Модель - всегда последняя колонка
            raw_model = row_vals[-1].strip()
            
            # ОЧИСТКА МОДЕЛИ: если там звездочка или что-то странное, считаем пустой
            if raw_model == '*' or raw_model == '-':
                model = ''
            else:
                model = raw_model

            # Иерархия - все колонки кроме последней
            hierarchy_vals = row_vals[:-1]
            
            actual_depth = 0
            
            # Проходим по уровням
            for i in range(len(hierarchy_vals)):
                val = str(hierarchy_vals[i]).strip()
                
                # ИСПРАВЛЕНИЕ ГЛАВНОЕ: Игнорируем '*' и пробелы
                if val == '*' or val == '-':
                    val = ''
                
                if val:
                    current_path[i] = val
                    actual_depth = i + 1
            
            # Если строка пустая (одни звездочки), пропускаем
            if actual_depth == 0 and not model:
                continue

            # Строим дерево
            current_node_ref = root
            for i in range(actual_depth):
                level_name = current_path[i]
                
                # Ищем ребенка
                found_child = None
                for child in current_node_ref['children']:
                    if child['name'] == level_name:
                        found_child = child
                        break
                
                if found_child:
                    # Если это последний уровень в строке и есть модель, обновляем
                    if i == actual_depth - 1 and model:
                        found_child['model'] = model
                    current_node_ref = found_child
                else:
                    # Создаем новый узел
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
        traceback.print_exc()
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

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        print("=== Начало обработки ===")
        if 'file' not in request.files:
            return jsonify({'error': 'Файл не найден'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Файл не выбран'}), 400

        print(f"Файл: {file.filename}")
        
        try:
            # Читаем Excel
            df = pd.read_excel(file, header=None)
            print(f"Размер таблицы: {df.shape}")
            
            table_data = df.fillna('').astype(str).values.tolist()
            
            # Строим
            root = build_smart_hierarchy(df)
            flat_data = flatten_hierarchy(root)
            
            stats = {
                'nodes': len(flat_data),
                'models': len([n for n in flat_data if n['Модель']]),
                'levels': max([n['Уровень'] for n in flat_data]) if flat_data else 0
            }
            
            tree_json = json.dumps(root, ensure_ascii=False)
            cache['current_file'] = (tree_json, flat_data, table_data, stats)
            
            print(f"Успех! Узлов: {stats['nodes']}")
            return jsonify({
                'tree_json': tree_json,
                'table_data': table_data,
                'stats': stats
            })
            
        except Exception as e:
            print(f"ОШИБКА: {e}")
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    return render_template('index.html')

@app.route('/export_json')
def export_json():
    if 'current_file' not in cache: return "Нет данных", 404
    tree_json, _, _, _ = cache['current_file']
    data = json.loads(tree_json)
    return send_file(
        BytesIO(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')),
        mimetype='application/json',
        as_attachment=True,
        download_name='hierarchy.json'
    )

@app.route('/export_csv')
def export_csv():
    if 'current_file' not in cache: return "Нет данных", 404
    _, flat_data, _, _ = cache['current_file']
    df = pd.DataFrame(flat_data)
    output = StringIO()
    df.to_csv(output, index=False, encoding='utf-8-sig', sep=';')
    return send_file(
        BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='hierarchy.csv'
    )

@app.route('/clear_cache', methods=['POST'])
def clear_cache():
    cache.clear()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print("Сервер: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)