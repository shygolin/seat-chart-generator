import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def read_student_names(txt_file):
    students = {}
    if os.path.exists(txt_file):
        with open(txt_file, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    students[parts[0]] = parts[1]
    return students

def generate_reportlab_from_data(seating_layout, students, output_pdf):
    c = canvas.Canvas(output_pdf, pagesize=A4)
    width, height = A4
    
    # --- 字型處理 ---
    # 優先尋找系統中的 Noto Sans CJK TC
    font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    font_name = "Helvetica" # 預設
    
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('NotoSans', font_path))
            font_name = 'NotoSans'
        except:
            pass
    
    # --- 繪製標題 ---
    c.setFont(font_name, 24)
    c.drawCentredString(width/2, height - 2*cm, "教室座位表")

    # --- 繪製座位邏輯 ---
    rows = len(seating_layout)
    cols = max(len(row) for row in seating_layout) if rows > 0 else 0
    
    cell_w = 2.5 * cm
    cell_h = 1.8 * cm
    gap = 0.3 * cm
    
    # 計算起始點讓表格置中
    start_x = (width - (cols * cell_w + (cols-1) * gap)) / 2
    start_y = height - 5*cm

    for r_idx, row in enumerate(reversed(seating_layout)):
        for c_idx, seat_num in enumerate(reversed(row)):
            x = start_x + c_idx * (cell_w + gap)
            y = start_y - r_idx * (cell_h + gap)
            
            # 畫格子
            c.setLineWidth(1)
            c.setStrokeColorRGB(0, 0, 0)
            c.rect(x, y, cell_w, cell_h)
            
            if seat_num and str(seat_num).strip():
                s_num = str(seat_num).strip()
                name = students.get(s_num, "")
                
                # 寫座號
                c.setFont(font_name, 10)
                c.drawString(x + 0.2*cm, y + cell_h - 0.5*cm, s_num)
                
                # 寫姓名 (垂直置中)
                c.setFont(font_name, 14)
                # 簡單計算文字寬度以置中
                name_w = c.stringWidth(name, font_name, 14)
                c.drawString(x + (cell_w - name_w)/2, y + 0.5*cm, name)

    # --- 繪製講台 ---
    podium_w = 8 * cm
    podium_h = 1 * cm
    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.rect((width-podium_w)/2, 2*cm, podium_w, podium_h, fill=1)
    c.setFillColorRGB(0, 0, 0)
    c.setFont(font_name, 16)
    c.drawCentredString(width/2, 2.3*cm, "講台")
    
    c.save()
    return True

# 為了相容原本的 server.py，保留這個空函式
def check_xelatex():
    return False
