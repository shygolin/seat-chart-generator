from flask import Flask, send_file, jsonify, request, send_from_directory
from flask_cors import CORS
import os
from seating_chart import (
    read_student_names, 
    check_xelatex, 
    generate_latex_from_data, 
    generate_reportlab_from_data
)

app = Flask(__name__, static_folder='.')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    """首頁"""
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """靜態檔案 (js, css)"""
    return send_from_directory(BASE_DIR, filename)

@app.route('/check-xelatex', methods=['GET'])
def check_status():
    """診斷用 API"""
    has_latex = check_xelatex()
    return jsonify({
        'has_xelatex': has_latex,
        'message': 'XeLaTeX is ready!' if has_latex else 'Using ReportLab fallback.'
    })

@app.route('/generate-pdf-from-json', methods=['POST'])
def generate_pdf():
    """接收 JSON 資料並生成 PDF"""
    try:
        data = request.get_json()
        if not data or 'seatingLayout' not in data:
            return jsonify({'success': False, 'message': '無效的資料格式'}), 400
        
        seating_layout = data['seatingLayout']
        txt_file = os.path.join(BASE_DIR, "座號對應名字.txt")
        output_pdf = os.path.join(BASE_DIR, "seating_chart_output.pdf")
        
        # 讀取名單
        students = read_student_names(txt_file)
        
        # 決定生成方式
        if check_xelatex():
            success = generate_latex_from_data(seating_layout, students, output_pdf)
        else:
            success = generate_reportlab_from_data(seating_layout, students, output_pdf)
            
        if success and os.path.exists(output_pdf):
            return send_file(output_pdf, as_attachment=True, download_name="座位表.pdf")
        else:
            return jsonify({'success': False, 'message': 'PDF 生成失敗'}), 500
            
    except Exception as e:
        print(f"Server Error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    # Railway 需要從環境變數讀取 PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
