from flask import Flask, send_file, jsonify, request, send_from_directory
from flask_cors import CORS
import os
# 確保從 seating_chart 匯入正確的函式
from seating_chart import read_student_names, generate_reportlab_from_data

# --- 1. 必須先定義 app，才能在下面使用 @app.route ---
app = Flask(__name__, static_folder='.')
CORS(app)

# 獲取專案根目錄
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- 2. 接下來才是定義路由 ---
@app.route('/')
def index():
    """提供前端頁面"""
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """提供靜態文件（JS, CSS）"""
    return send_from_directory(BASE_DIR, filename)

@app.route('/generate-pdf-from-json', methods=['POST'])
def generate_pdf():
    """接收 JSON 並生成 PDF"""
    try:
        data = request.get_json()
        if not data or 'seatingLayout' not in data:
            return jsonify({'success': False, 'message': '無效的資料格式'}), 400
            
        seating_layout = data['seatingLayout']
        txt_file = os.path.join(BASE_DIR, "座號對應名字.txt")
        output_pdf = os.path.join(BASE_DIR, "座位表.pdf")
        
        # 讀取學生姓名映射
        students = read_student_names(txt_file)
        
        # 使用 ReportLab 生成 PDF
        success = generate_reportlab_from_data(seating_layout, students, output_pdf)
        
        if success and os.path.exists(output_pdf):
            return send_file(output_pdf, as_attachment=True, download_name='座位表.pdf')
        else:
            return jsonify({'success': False, 'message': 'PDF 生成失敗'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/check-xelatex', methods=['GET'])
def check_status():
    """回傳狀態（現在固定為 false 因為我們改用 ReportLab）"""
    return jsonify({'has_xelatex': False, 'method': 'ReportLab'})

# --- 3. 啟動伺服器 ---
if __name__ == '__main__':
    # Railway 會自動分配 PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
