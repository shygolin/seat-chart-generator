// 座號→姓名映射（硬编码）
const nameMapping = {
    1: '何沛庭',
    2: '李安淇',
    5: '林冠伶',
    8: '洪煒庭',
    10: '許庭瑜',
    11: '陳芃安',
    12: '陳芊妤',
    13: '陳奕潔',
    14: '彭宥慈',
    15: '黃鈺甯',
    17: '蔡青霓',
    18: '王栩愷',
    19: '羊洺鋐',
    20: '何竑寬',
    23: '呂冠毅',
    24: '宋致霆',
    25: '李心澈',
    26: '沈昀謙',
    27: '林佑尚',
    28: '林昱宏',
    30: '施凱恩',
    31: '洪則謙',
    32: '郝祈恩',
    33: '高煜昕',
    34: '張瑜宸',
    35: '張睿軒',
    36: '曹家銨',
    37: '陳奕宏',
    38: '陳威宏',
    40: '陳昱翔',
    41: '陳昱瑋',
    42: '陳禹睿',
    43: '陳衍安',
    44: '黃子恒',
    45: '黃子維',
    46: '黃彥鈞',
    47: '黃嗣淇',
    49: '鄒佳祐',
    50: '劉展寧',
    51: '盧宏森',
    52: '盧品衡',
    53: '謝佳曄',
    55: '魏劭宸',
    56: '陳吉恩',
    57: '陳虹谷',
    58: '鄧欣閱',
    59: '魏妤真',
    60: '冼亮宇',
    61: '王瀚渝',
    62: '吳岳恩',
    63: '邱政喬',
    64: '許宇鋐'
};

// 座位表数据（7行×12列）
let seatingLayout = [];

// DOM 元素
const excelInput = document.getElementById('excelInput');
const saveBtn = document.getElementById('saveBtn');
const loadBtn = document.getElementById('loadBtn');
const resetBtn = document.getElementById('resetBtn');
const exportPdfBtn = document.getElementById('exportPdfBtn');
const seatingChart = document.getElementById('seatingChart');
const statusBar = document.getElementById('statusBar');
const statusText = document.getElementById('statusText');

// 显示状态信息
function showStatus(message, type = 'info') {
    statusText.textContent = message;
    statusBar.className = 'status-bar ' + type;
}

// Excel 文件上传处理
excelInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    showStatus('正在解析 Excel 文件...', 'info');

    try {
        const data = await file.arrayBuffer();
        const workbook = XLSX.read(data, { type: 'array' });
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        
        // 读取数据（7行×12列）
        seatingLayout = [];
        for (let row = 0; row < 7; row++) {
            const rowData = [];
            for (let col = 0; col < 12; col++) {
                const cellAddress = XLSX.utils.encode_cell({ r: row, c: col });
                const cell = worksheet[cellAddress];
                rowData.push(cell && cell.v ? parseInt(cell.v) : null);
            }
            seatingLayout.push(rowData);
        }

        renderSeatingChart();
        showStatus('座位表載入成功！', 'success');
        exportPdfBtn.disabled = false;
    } catch (error) {
        console.error('Excel 解析錯誤:', error);
        showStatus('Excel 文件解析失敗，請檢查文件格式。', 'error');
    }
});

// 渲染座位表（普通视角）
function renderSeatingChart() {
    seatingChart.innerHTML = '';

    for (let row = 0; row < 7; row++) {
        for (let col = 0; col < 12; col++) {
            const seatNumber = seatingLayout[row][col];
            
            // 只有在有座號的位置才创建座位格子（走道不显示）
            if (seatNumber !== null) {
                const seat = document.createElement('div');
                seat.className = 'seat';
                seat.dataset.row = row;
                seat.dataset.col = col;
                
                // 使用grid-column和grid-row精确定位
                seat.style.gridColumn = col + 1;
                seat.style.gridRow = row + 1;
                
                if (nameMapping[seatNumber]) {
                    seat.draggable = true;
                    seat.dataset.seatNumber = seatNumber;
                    seat.dataset.hasStudent = 'true';
                    
                    const name = nameMapping[seatNumber];
                    
                    seat.innerHTML = `
                        <div class="seat-number">${seatNumber}</div>
                        <div class="seat-name">${name}</div>
                    `;
                    
                    // 拖拽事件
                    seat.addEventListener('dragstart', handleDragStart);
                    seat.addEventListener('dragend', handleDragEnd);
                } else {
                    seat.classList.add('empty');
                    seat.dataset.hasStudent = 'false';
                }
                
                // 为所有座位添加放置事件（支持学生交换）
                seat.addEventListener('dragover', handleDragOver);
                seat.addEventListener('dragleave', handleDragLeave);
                seat.addEventListener('drop', handleDrop);
                
                seatingChart.appendChild(seat);
            }
        }
    }
}

// 拖拽功能
let draggedSeat = null;

function handleDragStart(e) {
    draggedSeat = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
}

function handleDragEnd(e) {
    this.classList.remove('dragging');
    document.querySelectorAll('.seat').forEach(seat => {
        seat.classList.remove('drag-over');
    });
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    // 不允许拖拽到自己
    if (this !== draggedSeat) {
        this.classList.add('drag-over');
    }
}

function handleDragLeave(e) {
    this.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    
    if (!draggedSeat) return;
    
    // 不允许拖拽到自己
    if (this === draggedSeat) return;
    
    const targetRow = parseInt(this.dataset.row);
    const targetCol = parseInt(this.dataset.col);
    const sourceRow = parseInt(draggedSeat.dataset.row);
    const sourceCol = parseInt(draggedSeat.dataset.col);
    
    const targetHasStudent = this.dataset.hasStudent === 'true';
    
    // 如果目标位置是空座位，直接移动
    if (!targetHasStudent) {
        seatingLayout[targetRow][targetCol] = seatingLayout[sourceRow][sourceCol];
        seatingLayout[sourceRow][sourceCol] = null;
    } 
    // 如果目标位置有学生，交换
    else {
        const temp = seatingLayout[targetRow][targetCol];
        seatingLayout[targetRow][targetCol] = seatingLayout[sourceRow][sourceCol];
        seatingLayout[sourceRow][sourceCol] = temp;
    }
    
    renderSeatingChart();
    showStatus('座位已更新！', 'success');
}

// 重置按钮
resetBtn.addEventListener('click', () => {
    seatingLayout = [];
    seatingChart.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📋</div><div>請上傳 Excel 座位表文件</div></div>';
    excelInput.value = '';
    showStatus('請上傳 Excel 座位表文件', 'info');
    exportPdfBtn.disabled = true;
});

// 匯出 PDF 按鈕（發送 JSON 到後端生成，無需 Excel）
exportPdfBtn.addEventListener('click', async () => {
    if (seatingLayout.length === 0) {
        showStatus('請先上傳座位表文件！', 'error');
        return;
    }
    
    showStatus('正在生成 PDF...', 'info');
    
    try {
        // 直接發送 JSON 數據到後端（使用相對路徑，同時支持本地和生產環境）
        const response = await fetch('/generate-pdf-from-json', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                seatingLayout: seatingLayout
            })
        });
        
        if (response.ok) {
            // 檢查是否是 PDF 檔案
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/pdf')) {
                // 下載 PDF
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = '座位表.pdf';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                showStatus('PDF 生成成功！', 'success');
            } else {
                const data = await response.json();
                showStatus(data.message || 'PDF 生成失敗', 'error');
            }
        } else {
            const data = await response.json();
            showStatus(data.message || 'PDF 生成失敗', 'error');
        }
    } catch (error) {
        console.error('生成 PDF 錯誤:', error);
        showStatus('PDF 生成失敗，請檢查伺服器是否正常運行', 'error');
    }
});

// 初始化
exportPdfBtn.disabled = true;
seatingChart.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📋</div><div>請上傳 Excel 座位表文件</div></div>';

// 保存功能
saveBtn.addEventListener('click', () => {
    if (seatingLayout.length === 0) {
        showStatus('沒有可儲存的座位表！', 'error');
        return;
    }
    
    const saveData = {
        seatingLayout: seatingLayout,
        timestamp: new Date().toISOString()
    };
    
    localStorage.setItem('seatingChart', JSON.stringify(saveData));
    showStatus('座位表已儲存！', 'success');
});

// 加载功能
loadBtn.addEventListener('click', () => {
    const savedData = localStorage.getItem('seatingChart');
    
    if (!savedData) {
        showStatus('沒有找到已儲存的座位表！', 'error');
        return;
    }
    
    try {
        const data = JSON.parse(savedData);
        seatingLayout = data.seatingLayout;
        renderSeatingChart();
        showStatus('座位表已載入！', 'success');
        exportPdfBtn.disabled = false;
    } catch (error) {
        console.error('載入失敗:', error);
        showStatus('載入失敗，請檢查儲存的資料。', 'error');
    }
});

// 保存到 Excel（供 Python 腳本使用）
function saveToExcelForPython() {
    const ws = XLSX.utils.aoa_to_sheet(seatingLayout);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Sheet1');
    XLSX.writeFile(wb, '座位表.xlsx');
}

// 頁面初始化時自動載入上次儲存的座位表
function autoLoadSavedData() {
    const savedData = localStorage.getItem('seatingChart');
    
    if (savedData) {
        try {
            const data = JSON.parse(savedData);
            if (data.seatingLayout && data.seatingLayout.length > 0) {
                seatingLayout = data.seatingLayout;
                renderSeatingChart();
                showStatus('已自動載入上次儲存的座位表', 'success');
                exportPdfBtn.disabled = false;
            }
        } catch (error) {
            console.error('自動載入失敗:', error);
        }
    }
}

// 頁面載入時執行自動載入
window.addEventListener('DOMContentLoaded', autoLoadSavedData);