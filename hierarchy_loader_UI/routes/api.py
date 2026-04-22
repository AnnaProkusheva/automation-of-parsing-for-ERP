from flask import Blueprint, request, jsonify
from services import ai_service

api_bp = Blueprint('api', __name__)

@api_bp.route('/search', methods=['POST'])
def api_search():
    data = request.json
    query = data.get('query', '')
    try:
        results = ai_service.search_real_links(query)
        return jsonify(results)
    except Exception as e:
        print(f"Критическая ошибка в /search: {e}")
        return jsonify([{"error": f"Внутренняя ошибка поиска: {str(e)}"}])

@api_bp.route('/api/analyze', methods=['POST'])
def api_analyze():
    """
    Надежная функция анализа.
    Если парсинг или ИИ упадут — вернет JSON с ошибкой, а не 500 HTML.
    """
    try:
        data = request.json
        url = data.get('url')
        model = data.get('model', '')
        
        if not url: 
            return jsonify({"error": "Не указан URL"}), 400
            
        # Вызываем функцию анализа (она может упасть на PDF или защищенном сайте)
        result = ai_service.parse_and_analyze(url, model)
        return jsonify(result)
        
    except Exception as e:
        # Ловим все, что пролетело мимо try-except в сервисе
        print(f"!!! КРИТИЧЕСКАЯ ОШИБКА В АНАЛИЗЕ !!!")
        print(f"URL: {url}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({"error": f"Не удалось проанализировать: {str(e)}"}), 500