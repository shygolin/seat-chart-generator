import openpyxl
import os
import subprocess
import shutil
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def read_student_names(txt_file):
    """讀取座號與姓名對應關係"""
    students = {}
    if os.path.exists(txt_file):
        with open(txt_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        students[parts[0]] = parts[1]
    return students

def check_xelatex():
    """檢查環境中是否有 xelatex 指令"""
    try:
        # 在 Railway Docker 環境中，這應該要回傳 True
        result = subprocess.run(['xelatex', '--version'], capture_output=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def generate_latex_from_data(seating_layout, students, output_pdf):
    """使用 XeLaTeX 生成高品質 PDF"""
    print("正在使用 XeLaTeX 生成高品質 PDF...")
    
    # 計算最大列數
    max_cols = max(len(row) for row in seating_layout) if seating_layout else 1

    # LaTeX 原始碼
    latex_content = r"""\documentclass[12pt,a4paper]{article}
\usepackage[UTF8, fontset=none]{ctex}
\usepackage{geometry}
\usepackage{array}
\usepackage{colortbl}
\usepackage{xcolor}
\usepackage{xeCJK}

% 設定 Linux 伺服器上的字型 (Dockerfile 中安裝的 fonts-noto-cjk)
\setCJKmainfont{Noto Sans CJK TC}

\geometry{left=1cm,right=1cm,top=2cm,bottom=2cm}
\newcolumntype{S}{>{\centering\arraybackslash}m{2.5cm}}
\pagestyle{empty}

\begin{document}
\begin{center}
\Huge \textbf{座位表} \\[1cm]
\Large
\begin{tabular}{|""" + ("S|" * max_cols) + r"""}
\hline
"""
    # 填入座位資料 (反轉陣列以符合講台在下方的邏輯)
    for row in reversed(seating_layout):
        row_cells = []
        for seat_num in reversed(row):
            if seat_num and str(seat_num).strip():
                s_num = str(seat_num).strip()
                name = students.get(s_num, "未知")
                # 在 LaTeX 中讓座號與姓名換行
                cell = f"\\textbf{{{s_num}}} \\\\[0.2cm] {name}"
                row_cells.append(cell)
            else:
                row_cells.append(" ")
        latex_content += " & ".join(row_cells) + r" \\ \hline" + "\n"

    latex_content += r"""\end{tabular}

\vspace{1.5cm}
\colorbox{lightgray!30}{\parbox{10cm}{\rule{0pt}{1cm}\centering \Huge \textbf{講台}\rule[-0.5cm]{0pt}{1cm}}}
\end{center}
\end{document}
"""

    # 寫入暫存 .tex 檔
    tex_filename = "temp_seating.tex"
    with open(tex_filename, "w", encoding="utf-8") as f:
        f.write(latex_content)

    try:
        # 執行 XeLaTeX
        subprocess.run(['xelatex', '-interaction=nonstopmode', tex_filename], check=True, capture_output=True)
        
        # 移動生成的 PDF
        if os.path.exists("temp_seating.pdf"):
            shutil.move("temp_seating.pdf", output_pdf)
            # 清理垃圾檔案
            for ext in ['.tex', '.log', '.aux']:
                if os.path.exists(f"temp_seating{ext}"):
                    os.remove(f"temp_seating{ext}")
            return True
    except subprocess.CalledProcessError as e:
        print(f"LaTeX 編譯失敗: {e.stderr.decode()}")
    return False

def generate_reportlab_from_data(seating_layout, students, output_pdf):
    """備援方案：使用 ReportLab 生成（當 LaTeX 不可用時）"""
    print("LaTeX 不可用，切換至 ReportLab 備援方案...")
    c = canvas.Canvas(output_pdf, pagesize=A4)
    width, height = A4
    
    # 嘗試載入中文字型
    font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('NotoSans', font_path))
        font_name = 'NotoSans'
    else:
        font_name = 'Helvetica'
        print("警告：找不到中文字型，PDF 中文將無法顯示")

    c.setFont(font_name, 20)
    c.drawCentredString(width/2, height - 2*cm, "座位表 (ReportLab 產生)")
    
    # 簡單的繪製邏輯
    y_start = height - 5*cm
    for i, row in enumerate(reversed(seating_layout)):
        for j, seat_num in enumerate(reversed(row)):
            if seat_num:
                name = students.get(str(seat_num), "")
                c.rect(2*cm + j*3*cm, y_start - i*2.5*cm, 2.5*cm, 2*cm)
                c.setFont(font_name, 10)
                c.drawString(2.1*cm + j*3*cm, y_start - i*2.5*cm + 1.2*cm, str(seat_num))
                c.setFont(font_name, 12)
                c.drawString(2.1*cm + j*3*cm, y_start - i*2.5*cm + 0.4*cm, name)
    
    c.save()
    return True
