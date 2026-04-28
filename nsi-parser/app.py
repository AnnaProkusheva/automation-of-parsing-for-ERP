import os
import tempfile
from flask import Flask, render_template, request, jsonify, send_file, after_this_request

from parser import PumpParser
from exporter import DataExporter

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pump-parser-secret-key'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

parser_instance = PumpParser(delay=2.0)
exporter_instance = DataExporter()

TEMP_DIR = tempfile.gettempdir()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/search', methods=['POST'])
def search_pumps():
    data = request.get_json()
    model_query = data.get('model', '').strip()
    max_pages = data.get('pages', 5)

    if not model_query:
        return jsonify({'error': 'Модель насоса не указана'}), 400

    try:
        results = parser_instance.search(model_query, max_pages=max_pages)
        return jsonify({
            'success': True,
            'count': len(results),
            'data': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export', methods=['POST'])
def export_data():
    data = request.get_json()
    format_type = data.get('format', 'excel')
    pumps = data.get('data', [])

    if not pumps:
        return jsonify({'error': 'Нет данных для экспорта'}), 400

    try:
        filename = exporter_instance.generate_filename(
            'xlsx' if format_type == 'excel' else 'json'
        )
        filepath = os.path.join(TEMP_DIR, filename)

        if format_type == 'excel':
            exporter_instance.to_excel(pumps, filepath)
        else:
            exporter_instance.to_json(pumps, filepath)

        @after_this_request
        def cleanup(response):
            try:
                os.remove(filepath)
            except Exception:
                pass
            return response

        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if format_type == 'excel' else 'application/json'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'pump-parser'})


if __name__ == '__main__':
    print("Запуск сервера: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)