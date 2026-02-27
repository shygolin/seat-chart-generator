import streamlit as st
import openpyxl
from io import BytesIO
import os
import pandas as pd
from seating_chart import generate_latex_from_data, generate_reportlab_from_data, check_xelatex, read_student_names

# 页面配置
st.set_page_config(page_title="座位表生成器", page_icon="🪑", layout="wide")

# 初始化 session state
if 'seating_layout' not in st.session_state:
    st.session_state.seating_layout = None
if 'selected_seat1' not in st.session_state:
    st.session_state.selected_seat1 = None
if 'selected_seat2' not in st.session_state:
    st.session_state.selected_seat2 = None

# 读取姓名映射
def load_name_mapping():
    try:
        return read_student_names("座號對應名字.txt")
    except:
        return {}

name_mapping = load_name_mapping()

# 标题
st.title("🪑 座位表生成器")
st.caption("點擊兩個座位進行交換 | Streamlit 版")

# 侧边栏
with st.sidebar:
    st.header("📋 操作")
    
    # 上传 Excel
    uploaded_file = st.file_uploader("上傳座位表 Excel", type=['xlsx', 'xls'])
    
    if uploaded_file:
        try:
            wb = openpyxl.load_workbook(BytesIO(uploaded_file.read()))
            ws = wb.active
            
            # 读取座位表数据
            seating_layout = []
            for row in ws.iter_rows():
                row_data = []
                for cell in row:
                    row_data.append(cell.value if cell.value is not None else None)
                seating_layout.append(row_data)
            
            st.session_state.seating_layout = seating_layout
            st.session_state.selected_seat1 = None
            st.session_state.selected_seat2 = None
            st.success("✅ 座位表載入成功！")
        except Exception as e:
            st.error(f"❌ 載入失敗: {e}")
    
    st.divider()
    
    # 显示已选择的座位
    if st.session_state.selected_seat1:
        r1, c1 = st.session_state.selected_seat1
        num1 = st.session_state.seating_layout[r1][c1]
        st.info(f"已選座位 1: 座號 {num1}")
    
    if st.session_state.selected_seat2:
        r2, c2 = st.session_state.selected_seat2
        num2 = st.session_state.seating_layout[r2][c2]
        st.warning(f"已選座位 2: 座號 {num2}")
    
    st.divider()
    
    # 交换按钮
    if st.session_state.selected_seat1 and st.session_state.selected_seat2:
        if st.button("🔄 交換選中的兩個座位", use_container_width=True, type="primary"):
            r1, c1 = st.session_state.selected_seat1
            r2, c2 = st.session_state.selected_seat2
            
            # 交换
            temp = st.session_state.seating_layout[r1][c1]
            st.session_state.seating_layout[r1][c1] = st.session_state.seating_layout[r2][c2]
            st.session_state.seating_layout[r2][c2] = temp
            
            st.session_state.selected_seat1 = None
            st.session_state.selected_seat2 = None
            st.rerun()
    
    # 清除选择
    if st.session_state.selected_seat1 or st.session_state.selected_seat2:
        if st.button("❌ 清除選擇", use_container_width=True):
            st.session_state.selected_seat1 = None
            st.session_state.selected_seat2 = None
            st.rerun()
    
    st.divider()
    
    # 生成 PDF 按钮
    if st.session_state.seating_layout:
        if st.button("📄 生成 PDF", use_container_width=True, type="primary"):
            with st.spinner("正在生成 PDF..."):
                txt_file = "座號對應名字.txt"
                output_pdf = "座位表.pdf"
                
                if not os.path.exists(txt_file):
                    st.error("❌ 座號對應名字.txt 不存在")
                else:
                    students = read_student_names(txt_file)
                    has_xelatex = check_xelatex()
                    
                    if has_xelatex:
                        success = generate_latex_from_data(st.session_state.seating_layout, students, output_pdf)
                    else:
                        success = generate_reportlab_from_data(st.session_state.seating_layout, students, output_pdf)
                    
                    if success and os.path.exists(output_pdf):
                        with open(output_pdf, 'rb') as f:
                            st.download_button(
                                label="⬇️ 下載 PDF",
                                data=f.read(),
                                file_name="座位表.pdf",
                                mime="application/pdf"
                            )
                    else:
                        st.error("❌ PDF 生成失敗")
    
    st.divider()
    
    # 重置按钮
    if st.button("🔄 重置座位表", use_container_width=True):
        st.session_state.seating_layout = None
        st.session_state.selected_seat1 = None
        st.session_state.selected_seat2 = None
        st.rerun()

# 主内容区
if st.session_state.seating_layout:
    st.subheader("座位表")
    
    num_rows = len(st.session_state.seating_layout)
    num_cols = len(st.session_state.seating_layout[0]) if num_rows > 0 else 0
    
    # 创建座位表网格
    for row_idx in range(num_rows):
        cols = st.columns(num_cols)
        
        for col_idx in range(num_cols):
            with cols[col_idx]:
                seat_num = st.session_state.seating_layout[row_idx][col_idx]
                
                if seat_num is not None:
                    seat_num_str = str(seat_num).strip()
                    name = name_mapping.get(seat_num_str, "")
                    
                    # 检查是否被选中
                    is_selected = (row_idx, col_idx) == st.session_state.selected_seat1 or (row_idx, col_idx) == st.session_state.selected_seat2
                    
                    # 座位按钮样式
                    if is_selected:
                        st.markdown(f"""
                        <div style='
                            background: rgba(102, 126, 234, 0.2);
                            border: 3px solid #667eea;
                            border-radius: 8px;
                            padding: 10px;
                            text-align: center;
                            height: 120px;
                            display: flex;
                            flex-direction: column;
                            justify-content: center;
                            cursor: pointer;
                        '>
                            <div style='font-size: 18px; font-weight: bold; color: #667eea; border-bottom: 1px solid #ddd; padding-bottom: 5px;'>{seat_num_str}</div>
                            <div style='font-size: 14px; color: #333; padding-top: 5px; writing-mode: vertical-rl; text-orientation: upright;'>{name}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style='
                            background: white;
                            border: 2px solid #e0e0e0;
                            border-radius: 8px;
                            padding: 10px;
                            text-align: center;
                            height: 120px;
                            display: flex;
                            flex-direction: column;
                            justify-content: center;
                            cursor: pointer;
                        '>
                            <div style='font-size: 18px; font-weight: bold; color: #667eea; border-bottom: 1px solid #ddd; padding-bottom: 5px;'>{seat_num_str}</div>
                            <div style='font-size: 14px; color: #333; padding-top: 5px; writing-mode: vertical-rl; text-orientation: upright;'>{name}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # 点击选择
                    if st.button(f"選擇", key=f"seat_{row_idx}_{col_idx}", use_container_width=True):
                        if st.session_state.selected_seat1 is None:
                            st.session_state.selected_seat1 = (row_idx, col_idx)
                        elif st.session_state.selected_seat2 is None:
                            st.session_state.selected_seat2 = (row_idx, col_idx)
                        else:
                            # 替换第二个选择
                            st.session_state.selected_seat2 = (row_idx, col_idx)
                        st.rerun()
                else:
                    # 空位
                    st.markdown("""
                    <div style='
                        background: #f5f5f5;
                        border: 2px dashed #e0e0e0;
                        border-radius: 8px;
                        height: 120px;
                    '></div>
                    """, unsafe_allow_html=True)
    
    # 讲台
    st.markdown("""
    <div style='
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 60px;
        border-radius: 10px;
        font-size: 20px;
        font-weight: 600;
        text-align: center;
        margin: 20px auto;
        max-width: 300px;
    '>講台</div>
    """, unsafe_allow_html=True)
else:
    st.info("👆 請在側邊欄上傳座位表 Excel 文件")