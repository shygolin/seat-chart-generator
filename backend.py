from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import openpyxl
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import tempfile
import shutil
import random
import json
from datetime import datetime
from dotenv import load_dotenv

app = FastAPI(title="座位表生成系统")


# 獲取數據目錄路徑（支持 Render 持久化存儲）
def get_data_dir():
    # Render 的持久化存儲路徑
    render_persistent_dir = os.getenv("RENDER_PERSISTENT_DIR")
    if render_persistent_dir:
        return os.path.join(render_persistent_dir, "data")
    # 本地開發使用當前目錄
    return "data"


class SeatCell(BaseModel):
    seat_num: str
    name: str


class SeatingChart(BaseModel):
    seating_chart: List[List[Optional[SeatCell]]]


class SeatingConfig(BaseModel):
    version: int
    timestamp: str
    academic_mode: bool
    seating_chart: List[List[Optional[SeatCell]]]
    couple_rules: List[List[str]]
    last_updated_by: str = "unknown"


class ConfigResponse(BaseModel):
    success: bool
    config: Optional[SeatingConfig] = None
    version: int = 0
    message: str = ""

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建临时目录
TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# 预设的座號對應姓名（从现有数据读取）
PRESET_STUDENTS = {
    "1": "何沛庭", "2": "李安淇", "5": "林冠伶", "8": "洪煒庭", "10": "許庭瑜",
    "11": "陳芃安", "12": "陳芊妤", "13": "陳奕潔", "14": "彭宥慈", "15": "黃鈺甯",
    "17": "蔡青霓", "18": "王栩愷", "19": "羊洺鋐", "20": "何竑寬", "23": "呂冠毅",
    "24": "宋致霆", "25": "李心澈", "26": "沈昀謙", "27": "林佑尚", "28": "林昱宏",
    "30": "施凱恩", "31": "洪則謙", "32": "郝祈恩", "33": "高煜昕", "34": "張瑜宸",
    "35": "張睿軒", "36": "曹家銨", "37": "陳奕宏", "38": "陳威宏", "40": "陳昱翔",
    "41": "陳昱瑋", "42": "陳禹睿", "43": "陳衍安", "44": "黃子恒", "45": "黃子維",
    "46": "黃彥鈞", "47": "黃嗣淇", "49": "鄒佳祐", "50": "劉展寧", "51": "盧宏森",
    "52": "盧品衡", "53": "謝佳曄", "55": "魏劭宸", "56": "陳吉恩", "57": "陳虹谷",
    "58": "鄧欣閱", "59": "魏妤真", "60": "冼亮宇", "61": "王瀚渝", "62": "吳岳恩",
    "63": "邱政喬", "64": "許宇鋐"
}

# 预设的教室座位配置（固定座號位置）
PRESET_SEATING_LAYOUT = [
    [32, None, 30, 31, None, 38, 51, None, 41, 61, None, 19],
    [56, None, 11, 8, None, 59, 60, None, 49, 52, None, 62],
    [12, None, 2, 5, None, 1, 46, None, 45, 35, None, 40],
    [15, None, 20, 36, None, 34, 25, None, 23, 17, None, 10],
    [57, None, 24, 33, None, 55, 13, None, 27, 47, None, 14],
    [63, None, 26, 44, None, 42, 58, None, 50, 64, None, 28],
    [None, None, 53, 18, None, 43, 37, None, None, None, None, None]
]


def read_student_names(txt_content):
    """读取座號和姓名对应关系"""
    students = {}
    for line in txt_content.split('\n'):
        line = line.strip()
        if line:
            parts = line.split('\t')
            if len(parts) >= 2:
                seat_num = parts[0]
                name = parts[1]
                students[seat_num] = name
    return students


def generate_pdf_from_data(excel_data, students, output_pdf):
    """生成座位表PDF"""
    # 创建PDF
    c = canvas.Canvas(output_pdf, pagesize=A4)
    width, height = A4

    # 设置字体
    font_name = None
    font_paths = [
        ('DFKai-SB', 'C:\\Windows\\Fonts\\kaiu.ttf')
    ]

    for name, path in font_paths:
        try:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont(name, path))
                font_name = name
                print(f"成功加载字体: {name}")
                break
        except Exception as e:
            print(f"加载字体失败 {name}: {e}")
            continue

    if font_name is None:
        print("警告: 无法加载中文字体，将使用默认字体")
        font_name = 'Helvetica'

    # 计算座位格大小
    cell_width = 1.5 * cm
    cell_height = 2.5 * cm
    margin_left = 1.5 * cm
    margin_top = 2.5 * cm

    # 老师视角：翻转行和列
    all_rows = excel_data
    for row_idx, row in enumerate(reversed(all_rows)):
        y = margin_top + row_idx * cell_height

        # 反转列顺序：从右往左
        for col_idx, cell_value in enumerate(reversed(row)):
            x = margin_left + col_idx * cell_width

            # 检查单元格是否有值
            if cell_value is not None:
                seat_num = str(cell_value).strip()

                # 绘制白色背景
                c.setFillColorRGB(1, 1, 1)
                c.rect(x, height - y - cell_height, cell_width, cell_height, fill=True, stroke=False)

                # 绘制座位格边框
                c.setStrokeColorRGB(0, 0, 0)
                c.setLineWidth(2)
                c.rect(x, height - y - cell_height, cell_width, cell_height, fill=False, stroke=True)

                # 绘制中间分隔线
                mid_y = height - y - cell_height * 0.35
                c.line(x, mid_y, x + cell_width, mid_y)

                # 绘制座號
                c.setFillColorRGB(0, 0, 0)
                c.setFont(font_name, 11)
                c.drawCentredString(x + cell_width/2, height - y - cell_height * 0.22, seat_num)

                # 绘制姓名（下方格子，竖排）
                c.setFillColorRGB(0, 0, 0)
                c.setFont(font_name, 12)
                if seat_num in students:
                    name = students[seat_num]
                    char_spacing = 0.45*cm
                    start_y = mid_y - 0.4*cm
                    for i, char in enumerate(name):
                        y_pos = start_y - i * char_spacing
                        c.drawCentredString(x + cell_width/2, y_pos, char)

    # 绘制讲台
    podium_width = 3 * cell_width
    podium_height = 1.0 * cm
    podium_x = margin_left + 4.5 * cell_width
    total_rows = len(all_rows)
    podium_y = margin_top + total_rows * cell_height + 0.3 * cm

    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.rect(podium_x, height - podium_y - podium_height, podium_width, podium_height, fill=True, stroke=False)

    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(2)
    c.rect(podium_x, height - podium_y - podium_height, podium_width, podium_height, fill=False, stroke=True)

    c.setFillColorRGB(0, 0, 0)
    c.setFont(font_name, 14)
    c.drawCentredString(podium_x + podium_width/2, height - podium_y - podium_height/2 - 0.05*cm, "講台")

    c.save()


@app.post("/api/upload")
async def upload_files(
    excel_file: UploadFile = File(...)
):
    """上传Excel文件，解析座位数据（使用预设的学生姓名）"""
    try:
        # 保存Excel文件
        excel_path = os.path.join(TEMP_DIR, excel_file.filename)
        with open(excel_path, "wb") as f:
            shutil.copyfileobj(excel_file.file, f)

        # 读取Excel数据
        wb = openpyxl.load_workbook(excel_path)
        ws = wb.active
        excel_data = []
        for row in ws.iter_rows():
            row_data = [cell.value for cell in row]
            excel_data.append(row_data)

        # 使用预设的学生数据
        students = PRESET_STUDENTS

        # 构建座位表数据（学生视角：保持原始排版，不翻转）
        seating_chart = []
        for row in excel_data:
            row_data = []
            for cell in row:
                if cell is not None:
                    seat_num = str(cell).strip()
                    name = students.get(seat_num, "")
                    row_data.append({
                        "seat_num": seat_num,
                        "name": name
                    })
                else:
                    row_data.append(None)
            seating_chart.append(row_data)

        return {
            "success": True,
            "excel_data": excel_data,
            "seating_chart": seating_chart,
            "message": "文件上传成功"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-pdf")
async def generate_pdf(request: SeatingChart):
    """生成座位表PDF"""
    try:
        seating_chart = request.seating_chart

        # 创建临时PDF文件
        pdf_path = os.path.join(TEMP_DIR, "seat_chart.pdf")

        # 构建Excel数据格式
        excel_data = []
        for row in seating_chart:
            row_data = []
            for cell in row:
                if cell is not None:
                    row_data.append(cell.seat_num)
                else:
                    row_data.append(None)
            excel_data.append(row_data)

        # 构建学生字典
        students = {}
        for row in seating_chart:
            for cell in row:
                if cell is not None and cell.name:
                    students[cell.seat_num] = cell.name

        # 生成PDF
        generate_pdf_from_data(excel_data, students, pdf_path)

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="座位表.pdf"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/randomize")
async def randomize_seating(request: SeatingChart):
    """随机分配学生座位"""
    try:
        seating_chart = request.seating_chart

        # 收集所有学生姓名
        student_names = []
        for row in seating_chart:
            for cell in row:
                if cell is not None and cell.name:
                    student_names.append(cell.name)

        # 随机打乱学生姓名
        random.shuffle(student_names)

        # 重新分配学生姓名到座位表
        name_index = 0
        randomized_chart = []
        for row in seating_chart:
            new_row = []
            for cell in row:
                if cell is not None:
                    if cell.name and name_index < len(student_names):
                        new_row.append({
                            "seat_num": cell.seat_num,
                            "name": student_names[name_index]
                        })
                        name_index += 1
                    else:
                        new_row.append({
                            "seat_num": cell.seat_num,
                            "name": cell.name
                        })
                else:
                    new_row.append(None)
            randomized_chart.append(new_row)

        return {
            "success": True,
            "seating_chart": randomized_chart,
            "message": "座位表随机分配成功"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/get-preset-layout")
async def get_preset_layout():
    """获取预设的教室座位配置"""
    # 构建座位表数据（学生视角：保持原始排版）
    seating_chart = []
    for row in PRESET_SEATING_LAYOUT:
        row_data = []
        for cell in row:
            if cell is not None:
                seat_num = str(cell).strip()
                name = PRESET_STUDENTS.get(seat_num, "")
                row_data.append({
                    "seat_num": seat_num,
                    "name": name
                })
            else:
                row_data.append(None)
        seating_chart.append(row_data)

    return {
        "success": True,
        "seating_chart": seating_chart,
        "message": "获取预设教室配置成功"
    }


@app.get("/api/get-couple-rules")
async def get_couple_rules():
    """获取不能坐在一起的座號對列表"""
    try:
        couple_file = "couple.txt"
        couples = []

        with open(couple_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split(',')
                    if len(parts) == 2:
                        couple = [parts[0].strip(), parts[1].strip()]
                        couples.append(couple)

        return {
            "success": True,
            "couples": couples,
            "message": "获取座號對规则成功"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def cleanup_old_backups(config_dir, keep_count=10):
    """清理舊的備份文件，保留最新的 keep_count 個"""
    import glob
    backups = glob.glob(os.path.join(config_dir, "seating_config_backup_*.json"))
    backups.sort(reverse=True)

    for backup in backups[keep_count:]:
        try:
            os.remove(backup)
        except:
            pass


@app.post("/api/save-config")
async def save_config(config: SeatingConfig):
    """保存座位表配置到文件"""
    CONFIG_DIR = get_data_dir()
    CONFIG_FILE = os.path.join(CONFIG_DIR, "seating_config.json")

    # 確保目錄存在
    os.makedirs(CONFIG_DIR, exist_ok=True)

    try:
        # 如果是第一次保存，讀取當前版本號
        current_version = 0
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    current_data = json.load(f)
                    current_version = current_data.get('version', 0)
            except:
                pass

        # 檢查版本號（並發控制）
        if config.version != current_version:
            raise HTTPException(
                status_code=409,  # Conflict
                detail=f"配置已被其他用戶更新，請重新載入後再保存。當前版本：v{current_version}，您的版本：v{config.version}"
            )

        # 更新版本號和時間戳
        new_version = current_version + 1
        config.version = new_version
        config.timestamp = datetime.utcnow().isoformat()

        # 備份舊配置
        if current_version > 0:
            backup_file = os.path.join(
                CONFIG_DIR,
                f"seating_config_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_v{current_version}.json"
            )
            shutil.copy2(CONFIG_FILE, backup_file)

            # 清理舊備份（保留最近10個）
            cleanup_old_backups(CONFIG_DIR)

        # 保存新配置
        config_dict = config.dict()
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "version": new_version,
            "timestamp": config.timestamp,
            "message": "配置保存成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存配置失敗: {str(e)}")


@app.get("/api/load-config")
async def load_config():
    """載入座位表配置"""
    CONFIG_FILE = os.path.join(get_data_dir(), "seating_config.json")

    try:
        if not os.path.exists(CONFIG_FILE):
            return {
                "success": True,
                "config": None,
                "version": 0,
                "message": "尚無保存的配置"
            }

        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        return {
            "success": True,
            "config": config_data,
            "version": config_data.get('version', 0),
            "message": "配置載入成功"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"載入配置失敗: {str(e)}")


@app.get("/api/check-config-update")
async def check_config_update(current_version: int = 0):
    """檢查是否有新版本的配置"""
    CONFIG_FILE = os.path.join(get_data_dir(), "seating_config.json")

    try:
        if not os.path.exists(CONFIG_FILE):
            return {
                "has_update": False,
                "version": 0
            }

        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        latest_version = config_data.get('version', 0)

        return {
            "has_update": latest_version > current_version,
            "version": latest_version,
            "timestamp": config_data.get('timestamp', ''),
            "academic_mode": config_data.get('academic_mode', False)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"檢查更新失敗: {str(e)}")


@app.get("/")
async def root():
    return {"message": "座位表生成系统API"}


if __name__ == "__main__":
    import uvicorn
    # 從環境變量獲取端口，默認為 8000
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
