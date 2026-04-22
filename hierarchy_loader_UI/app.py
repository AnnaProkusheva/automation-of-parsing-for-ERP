# app.py

from flask import Flask, jsonify
from routes.main import main_bp
from routes.api import api_bp

app = Flask(__name__)

# --- ДОБАВИТЬ ЭТО (Ловец всех ошибок) ---
@app.errorhandler(Exception)
def handle_exception(e):
    # Выводим полную ошибку в терминал
    import traceback
    print("!!! ВНИМАНИЕ: КРИТИЧЕСКАЯ ОШИБКА НА СЕРВЕРЕ !!!")
    traceback.print_exc()
    
    # Отдаем JSON вместо HTML
    return jsonify({"error": f"Внутренняя ошибка сервера: {str(e)}"}), 500
# ------------------------------------

app.register_blueprint(main_bp)
app.register_blueprint(api_bp)

if __name__ == '__main__':
    print("Сервер запущен: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)