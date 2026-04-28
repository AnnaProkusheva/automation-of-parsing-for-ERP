import os
import tempfile
from flask import Flask, render_template, request, jsonify, send_file, after_this_request

from parser import PumpParser, ElcomParser
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
    max_pages = data.get('pages', 30)
    fetch_details = data.get('fetch_details', False)  # Опционально: парсить детальные страницы

    if not model_query:
        return jsonify({'error': 'Модель не указана'}), 400

    try:
        print(f"\n{'=' * 60}")
        print(f"🔍 Поиск: '{model_query}'")
        print(f"{'=' * 60}")

        # Источник 1: nasoscentr.ru
        print("\n📍 Источник 1: nasoscentr.ru")
        results = parser_instance.search(model_query, max_pages=max_pages)

        if results:
            print(f"✅ Найдено: {len(results)}")
        else:
            # Источник 2: prm.elcomspb.ru
            print("\n📍 Источник 2: prm.elcomspb.ru")
            print(f"   fetch_details={fetch_details} (парсинг детальных страниц: {'вкл' if fetch_details else 'выкл'})")
            elcom_parser = ElcomParser(delay=1.5)
            results = elcom_parser.search(model_query, max_pages=max_pages, fetch_details=fetch_details)

        print(f"\n📊 Итого: {len(results)} результатов")
        print(f"{'=' * 60}\n")

        return jsonify({
            'success': True,
            'count': len(results),
            'data': results
        })
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
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