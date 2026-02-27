@app.route('/generate-pdf-from-json', methods=['POST'])
def generate_pdf():
    data = request.get_json()
    seating_layout = data.get('seatingLayout', [])
    txt_file = os.path.join(BASE_DIR, "座號對應名字.txt")
    output_pdf = os.path.join(BASE_DIR, "座位表.pdf")
    
    students = read_student_names(txt_file)
    
    # 直接使用 ReportLab
    success = generate_reportlab_from_data(seating_layout, students, output_pdf)
    
    if success:
        return send_file(output_pdf, as_attachment=True)
    return jsonify({'error': 'Failed'}), 500
