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
    
    # --- 字型處理邏輯 ---
    font_name = "Helvetica"
    # 優先序 1: 專案目錄下的字型檔 (最保險)
    local_font = os.path.join(os.path.dirname(__file__), "font.ttc")
    # 優先序 2: Linux 系統字型 (Dockerfile 安裝的)
    linux_font = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    
    target_font = local_font if os.path.exists(local_font) else linux_font

    if os.path.exists(target_font):
        try:
            pdfmetrics.registerFont(TTFont('CustomFont', target_font))
            font_name = 'CustomFont'
        except Exception as e:
            print(f"字型載入失敗: {e}")
    
    # --- 開始繪製 ---
    # 標題
    c.setFont(font_name, 22)
    c.drawCentredString(width/2, height - 2*cm, "教室座位表")

    rows = len(seating_layout)
    cols = max(len(row) for row in seating_layout) if rows > 0 else 0
    
    # 設定格子大小 (依照寬度自動調整)
    cell_w = min(3.5 * cm, (width - 4*cm) / max(cols, 1))
    cell_h = 1.8 * cm
    gap = 0.2 * cm
    
    # 計算置中起始位置
    start_x = (width - (cols * cell_w + (cols-1) * gap)) / 2
    start_y = height - 5*cm

    # 繪製座位
    for r_idx, row in enumerate(reversed(seating_layout)):
        for c_idx, seat_num in enumerate(reversed(row)):
            x = start_x + c_idx * (cell_w + gap)
            y = start_y - r_idx * (cell_h + gap)
            
            # 畫外框
            c.setLineWidth(1)
            c.rect(x, y, cell_w, cell_h)
            
            if seat_num and str(seat_num).strip():
                s_num = str(seat_num).strip()
                name = students.get(s_num, "無名")
                
                # 寫座號 (左上角)
                c.setFont(font_name, 9)
                c.drawString(x + 0.15*cm, y + cell_h - 0.4*cm, s_num)
                
                # 寫姓名 (中央)
                c.setFont(font_name, 12)
                name_w = c.stringWidth(name, font_name, 12)
                c.drawString(x + (cell_w - name_w)/2, y + 0.5*cm, name)

    # 繪製講台 (底部)
    podium_w = 6 * cm
    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.rect((width-podium_w)/2, 2*cm, podium_w, 1*cm, fill=1)
    c.setFillColorRGB(0, 0, 0)
    c.setFont(font_name, 14)
    c.drawCentredString(width/2, 2.3*cm, "講台")
    
    c.save()
    return True

# 為了 server.py 呼叫不報錯，保留空函式
def check_xelatex(): return False
def generate_latex_from_data(*args): return False
