import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def read_student_names(txt_file):
    """讀取座號與姓名對應關係 (Tab 分隔)"""
    students = {}
    if os.path.exists(txt_file):
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            students[str(parts[0])] = parts[1]
        except Exception as e:
            print(f"讀取名單檔案失敗: {e}")
    return students

def generate_reportlab_from_data(seating_layout, students, output_pdf):
    """使用 ReportLab 生成 PDF，支援中文與固定排版"""
    c = canvas.Canvas(output_pdf, pagesize=A4)
    width, height = A4
    
    # --- 1. 字型設定 (Linux 伺服器標準路徑) ---
    # 對應 Dockerfile 中的 fonts-noto-cjk
    font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    font_name = "Helvetica" # 預設（不支援中文）
    
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('NotoSans', font_path))
            font_name = 'NotoSans'
        except Exception as e:
            print(f"字型註冊失敗: {e}")
    else:
        print(f"警告: 找不到字型檔 {font_path}，中文將無法顯示")

    # --- 2. 繪製標題 ---
    c.setFont(font_name, 24)
    c.drawCentredString(width/2, height - 2*cm, "教室座位表")

    # --- 3. 計算座位佈局 ---
    if not seating_layout:
        c.setFont(font_name, 12)
        c.drawCentredString(width/2, height/2, "無座位資料")
        c.save()
        return True

    rows = len(seating_layout)
    cols = max(len(row) for row in seating_layout) if rows > 0 else 0
    
    # 格子大小設定 (A4 寬度約 21cm，扣掉邊距)
    cell_w = min(3.0 * cm, (width - 3*cm) / max(cols, 1))
    cell_h = 1.8 * cm
    gap = 0.2 * cm
    
    # 計算整體表格寬度以進行置中
    total_table_w = cols * cell_w + (cols - 1) * gap
    start_x = (width - total_table_w) / 2
    start_y = height - 5*cm # 從上方往下繪製

    # --- 4. 繪製座位格 ---
    # 注意：ReportLab 的 y 軸是從底部往上算 (0 是底部)
    for r_idx, row in enumerate(reversed(seating_layout)):
        for c_idx, seat_num in enumerate(reversed(row)):
            x = start_x + c_idx * (cell_w + gap)
            y = start_y - r_idx * (cell_h + gap)
            
            # 繪製方框
            c.setLineWidth(1)
            c.setStrokeColorRGB(0, 0, 0)
            c.rect(x, y, cell_w, cell_h, fill=0)
            
            if seat_num and str(seat_num).strip():
                s_num = str(seat_num).strip()
                name = students.get(s_num, "")
                
                # 寫座號 (左上角小字)
                c.setFont(font_name, 9)
                c.drawString(x + 0.15*cm, y + cell_h - 0.4*cm, s_num)
                
                # 寫姓名 (中央大字)
                c.setFont(font_name, 13)
                # 計算姓名寬度以水平置中
                name_w = c.stringWidth(name, font_name, 13)
                c.drawString(x + (cell_w - name_w)/2, y + 0.5*cm, name)

    # --- 5. 繪製講台 (固定在頁面下方) ---
    podium_w = 7 * cm
    podium_h = 1 * cm
    podium_x = (width - podium_w) / 2
    podium_y = 2 * cm
    
    c.setStrokeColorRGB(0, 0, 0)
    c.setFillColorRGB(0.9, 0.9, 0.9) # 淺灰色背景
    c.rect(podium_x, podium_y, podium_w, podium_h, fill=1)
    
    c.setFillColorRGB(0, 0, 0) # 切換回黑色寫字
    c.setFont(font_name, 16)
    c.drawCentredString(width/2, podium_y + 0.3*cm, "講台")
    
    c.save()
    return True

# 保留這些空函式以確保 server.py 呼叫時不會報錯
def check_xelatex():
    return False

def generate_latex_from_data(*args, **kwargs):
    return False
