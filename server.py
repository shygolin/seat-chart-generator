from flask import Flask, send_file, jsonify, request, send_from_directory
from flask_cors import CORS
import os
from seating_chart import generate_latex_from_data, generate_reportlab_from_data, check_xelatex, read_student_names

app = Flask(__name__, static_folder='.')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/generate-pdf-from-json', methods=['POST'])
def generate_pdf_from_json():
    data = request.get_json()
    seating_layout = data.get('seatingLayout', [])
    txt_file = os.path.join(BASE_DIR, "座號對應名字.txt")
    output_pdf = os.path.join(BASE_DIR, "座位表.pdf")
    
    students = read_student_names(txt_file)
    
    if check_xelatex():
        success = generate_latex_from_data(seating_layout, students, output_pdf)
    else:
        success = generate_reportlab_from_data(seating_layout, students, output_pdf)
    
    if success:
        return send_file(output_pdf, as_attachment=True)
    return jsonify({'error': 'Failed to generate PDF'}), 500

@app.route('/check-xelatex')
def check():
    return jsonify({'has_xelatex': check_xelatex()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
