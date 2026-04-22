from flask import Blueprint, render_template, request, send_file, jsonify
from services import excel_parser
from io import BytesIO, StringIO
import pandas as pd
import json

main_bp = Blueprint('main', __name__)

# ВРЕМЕННЫЙ КЭШ (в идеале использовать Redis или базу данных)
cache = {}

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'Файл не найден'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Файл не выбран'}), 400

        try:
            df = pd.read_excel(file, header=None)
            table_data = df.fillna('').astype(str).values.tolist()
            
            root = excel_parser.build_smart_hierarchy(df)
            flat_data = excel_parser.flatten_hierarchy(root)
            
            stats = {
                'nodes': len(flat_data),
                'models': len([n for n in flat_data if n['Модель']]),
                'levels': max([n['Уровень'] for n in flat_data]) if flat_data else 0
            }
            
            tree_json = json.dumps(root, ensure_ascii=False)
            cache['current_file'] = (tree_json, flat_data, table_data, stats)
            
            return jsonify({
                'tree_json': tree_json,
                'table_data': table_data,
                'stats': stats
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return render_template('index.html')

@main_bp.route('/export_json')
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

@main_bp.route('/export_csv')
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

@main_bp.route('/clear_cache', methods=['POST'])
def clear_cache():
    cache.clear()
    return jsonify({'status': 'ok'})