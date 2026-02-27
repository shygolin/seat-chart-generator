from flask import Flask, send_file, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import subprocess
from seating_chart import generate_latex, generate_reportlab, check_xelatex, read_student_names, generate_latex_from_data, generate_reportlab_from_data
import openpyxl

app = Flask(__name__, static_folder='.')
CORS(app)  # 啟用 CORS 支援

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    """提供前端页面"""
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """提供静态文件（JS, CSS）"""
    return send_from_directory(BASE_DIR, filename)

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    """生成 PDF 並返回（從 Excel 檔案讀取）"""
    try:
        excel_file = os.path.join(BASE_DIR, "座位表.xlsx")
        txt_file = os.path.join(BASE_DIR, "座號對應名字.txt")
        output_pdf = os.path.join(BASE_DIR, "座位表.pdf")
        
        # 檢查檔案是否存在
        if not os.path.exists(excel_file):
            return jsonify({'success': False, 'message': '座位表.xlsx 不存在，請先在網頁上匯出 Excel'}), 400
        
        if not os.path.exists(txt_file):
            return jsonify({'success': False, 'message': '座號對應名字.txt 不存在'}), 400
        
        # 檢查是否安裝了 XeLaTeX
        has_xelatex = check_xelatex()
        
        if has_xelatex:
            # 使用 LaTeX 生成 PDF
            success = generate_latex(excel_file, txt_file, output_pdf)
        else:
            # 使用 ReportLab 生成 PDF
            success = generate_reportlab(excel_file, txt_file, output_pdf)
        
        if success and os.path.exists(output_pdf):
            return send_file(output_pdf, as_attachment=True, download_name='座位表.pdf')
        else:
            return jsonify({'success': False, 'message': 'PDF 生成失敗'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/generate-pdf-from-json', methods=['POST'])
def generate_pdf_from_json():
    """直接從 JSON 數據生成 PDF（無需 Excel 檔案）"""
    try:
        # 獲取 JSON 數據
        data = request.get_json()
        
        if not data or 'seatingLayout' not in data:
            return jsonify({'success': False, 'message': '缺少座位表數據'}), 400
        
        seating_layout = data['seatingLayout']
        txt_file = os.path.join(BASE_DIR, "座號對應名字.txt")
        output_pdf = os.path.join(BASE_DIR, "座位表.pdf")
        
        # 檢查姓名映射檔案是否存在
        if not os.path.exists(txt_file):
            return jsonify({'success': False, 'message': '座號對應名字.txt 不存在'}), 400
        
        # 讀取學生姓名映射
        students = read_student_names(txt_file)
        
        # 檢查是否安裝了 XeLaTeX
        has_xelatex = check_xelatex()
        
        if has_xelatex:
            # 使用 LaTeX 生成 PDF
            success = generate_latex_from_data(seating_layout, students, output_pdf)
        else:
            # 使用 ReportLab 生成 PDF
            success = generate_reportlab_from_data(seating_layout, students, output_pdf)
        
        if success and os.path.exists(output_pdf):
            return send_file(output_pdf, as_attachment=True, download_name='座位表.pdf')
        else:
            return jsonify({'success': False, 'message': 'PDF 生成失敗'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/check-xelatex', methods=['GET'])
def check_xelatex_status():
    """檢查 XeLaTeX 是否已安裝"""
    has_xelatex = check_xelatex()
    return jsonify({'has_xelatex': has_xelatex})

if __name__ == '__main__':
    print("=" * 50)
    print("座位表生成器伺服器")
    print("=" * 50)
    print("\n伺服器已啟動...")
    print("網頁版網址: http://localhost:5000")
    print("API 端點: http://localhost:5000/generate-pdf (POST)")
    print()
    app.run(host='127.0.0.1', port=5000, debug=True)