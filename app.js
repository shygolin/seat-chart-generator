let currentSeatingChart = null;
let coupleRules = [];
let currentMode = '一般'; // 默認一般模式

// 全局變量 - 用於配置同步
let currentConfigVersion = 0;
let autoSyncInterval = null;
let lastConfigData = null;

// 用戶模式管理
let currentUserMode = 'admin'; // 'admin' 或 'user'

// 切換用戶模式
function toggleUserMode() {
    const toggleBtn = document.getElementById('userModeToggle');
    const body = document.body;

    if (currentUserMode === 'admin') {
        // 切換到用戶模式
        currentUserMode = 'user';
        toggleBtn.textContent = '👤 用戶';
        toggleBtn.classList.remove('admin-mode');
        toggleBtn.classList.add('user-mode');
        body.classList.remove('mode-admin');
        body.classList.add('mode-user');

        // 停止自動保存
        stopAutoSave();

        // 開啟自動同步（接收管理員更新）
        startAutoSync();

        showInfo('已切換到用戶模式 - 只能查看和拖曳對調');
    } else {
        // 切換到管理員模式
        currentUserMode = 'admin';
        toggleBtn.textContent = '🔧 管理員';
        toggleBtn.classList.remove('user-mode');
        toggleBtn.classList.add('admin-mode');
        body.classList.remove('mode-user');
        body.classList.add('mode-admin');

        // 重新載入最新配置
        loadSavedConfig();

        showInfo('已切換到管理員模式 - 可以修改和保存配置');
    }
}

// 自動保存配置（管理員模式）
let autoSaveTimeout = null;
function scheduleAutoSave() {
    if (currentUserMode !== 'admin') return;

    if (autoSaveTimeout) {
        clearTimeout(autoSaveTimeout);
    }

    autoSaveTimeout = setTimeout(() => {
        saveCurrentConfig();
    }, 1000); // 1秒後自動保存
}

function stopAutoSave() {
    if (autoSaveTimeout) {
        clearTimeout(autoSaveTimeout);
        autoSaveTimeout = null;
    }
}

// 顯示右鍵菜單
function showContextMenu(x, y) {
    const contextMenu = document.getElementById('contextMenu');

    // 更新菜單項文字
    const menuText = document.getElementById('menuAcademicModeText');
    if (currentMode === '學藝') {
        menuText.textContent = '關閉學藝模式';
    } else {
        menuText.textContent = '開啟學藝模式';
    }

    // 調整菜單位置（防止超出屏幕）
    const menuWidth = 200;
    const menuHeight = 150;

    if (x + menuWidth > window.innerWidth) {
        x = window.innerWidth - menuWidth - 10;
    }
    if (y + menuHeight > window.innerHeight) {
        y = window.innerHeight - menuHeight - 10;
    }

    contextMenu.style.left = x + 'px';
    contextMenu.style.top = y + 'px';
    contextMenu.style.display = 'block';
}

// 隱藏右鍵菜單
function hideContextMenu() {
    const contextMenu = document.getElementById('contextMenu');
    contextMenu.style.display = 'none';
}

// 頁面加载时获取预设教室配置
window.onload = function() {
    // 初始化默認模式為管理員模式
    const body = document.body;
    body.classList.add('mode-admin');

    // 先嘗試載入保存的配置
    loadSavedConfig().then(() => {
        // 如果沒有保存的配置，載入預設佈局
        if (!currentSeatingChart) {
            loadPresetLayout();
        }
    }).catch(() => {
        // 載入失敗，使用預設佈局
        loadPresetLayout();
    });

    loadCoupleRules();

    // 啟動自動同步
    startAutoSync();
};

// 切換學藝模式
function toggleAcademicMode() {
    // 隱藏菜單
    hideContextMenu();

    if (currentMode === '一般') {
        currentMode = '學藝';
    } else {
        currentMode = '一般';
    }

    // 更新按鈕狀態
    const modeBtn = document.getElementById('modeToggleBtn');
    if (currentMode === '學藝') {
        modeBtn.textContent = '🎓 學藝模式：開啟';
        modeBtn.classList.add('active');
    } else {
        modeBtn.textContent = '🎓 學藝模式：關閉';
        modeBtn.classList.remove('active');
    }

    // 更新權限顯示
    updateModePermissions();

    // 重新渲染座位表以更新拖曳功能
    if (currentSeatingChart) {
        renderSeatingChart(currentSeatingChart);
    }

    // 顯示模式切換提示
    showModeInfo();

    // 自動保存配置
    saveCurrentConfig();
}

// 顯示當前模式信息
function showModeInfo() {
    const modeInfo = document.getElementById('modeInfo');
    if (currentMode === '學藝') {
        modeInfo.innerHTML = '<strong>學藝模式已開啟</strong>：可使用 PDF 下載功能';
    } else {
        modeInfo.innerHTML = '<strong>學藝模式已關閉</strong>：無法使用 PDF 下載功能';
    }
}

// 根據當前模式更新權限
function updateModePermissions() {
    const pdfBtn = document.querySelector('.btn-success'); // 下載 PDF 按鈕

    // 用戶模式下，PDF 功能總是可用
    if (currentUserMode === 'user') {
        pdfBtn.disabled = false;
        pdfBtn.style.opacity = '1';
        pdfBtn.title = '';
    } else if (currentMode === '學藝') {
        // 管理員模式 + 學藝模式：PDF 功能可用
        pdfBtn.disabled = false;
        pdfBtn.style.opacity = '1';
        pdfBtn.title = '';
    } else {
        // 管理員模式 + 一般模式：禁用 PDF 功能
        pdfBtn.disabled = true;
        pdfBtn.style.opacity = '0.5';
        pdfBtn.title = '請開啟學藝模式後使用此功能';
    }
}

// 更新模式按鈕
function updateModeButton() {
    const modeBtn = document.getElementById('modeToggleBtn');
    if (currentMode === '學藝') {
        modeBtn.textContent = '🎓 學藝模式：開啟';
        modeBtn.classList.add('active');
    } else {
        modeBtn.textContent = '🎓 學藝模式：關閉';
        modeBtn.classList.remove('active');
    }
}

// 獲取客戶端標識
function getClientId() {
    // 生成一個簡單的客戶端標識
    let clientId = localStorage.getItem('seating_client_id');
    if (!clientId) {
        clientId = 'user_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('seating_client_id', clientId);
    }
    return clientId;
}

// 保存當前配置
async function saveCurrentConfig() {
    // 用戶模式下不保存配置
    if (currentUserMode === 'user') {
        console.log('用戶模式下不保存配置');
        return;
    }

    if (!currentSeatingChart) {
        return;
    }

    try {
        const config = {
            version: currentConfigVersion,
            timestamp: new Date().toISOString(),
            academic_mode: currentMode === '學藝',
            seating_chart: currentSeatingChart,
            couple_rules: coupleRules,
            last_updated_by: getClientId()
        };

        const response = await fetch('/api/save-config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });

        if (!response.ok) {
            if (response.status === 409) {
                const error = await response.json();
                if (confirm(`⚠️ ${error.detail}\n\n是否要重新載入最新配置？`)) {
                    await loadSavedConfig();
                }
            }
            return;
        }

        const result = await response.json();
        currentConfigVersion = result.version;
        lastConfigData = config;

        console.log('✅ 配置保存成功！版本號：v' + result.version);

    } catch (error) {
        console.error('保存配置失敗：' + error.message);
    }
}

// 載入保存的配置
async function loadSavedConfig() {
    try {
        const response = await fetch('/api/load-config');
        if (!response.ok) {
            throw new Error('載入配置失敗');
        }

        const result = await response.json();

        if (!result.config) {
            console.log('ℹ️ 尚無保存的配置');
            return;
        }

        const config = result.config;
        currentConfigVersion = result.version;
        lastConfigData = config;

        // 應用配置
        currentSeatingChart = config.seating_chart;
        coupleRules = config.couple_rules || [];

        // 更新學藝模式
        if (config.academic_mode) {
            currentMode = '學藝';
        } else {
            currentMode = '一般';
        }
        updateModeButton();
        updateModePermissions();
        showModeInfo();

        // 重新渲染
        renderSeatingChart(currentSeatingChart);

        // 確保預覽區顯示
        const previewSection = document.getElementById('previewSection');
        if (previewSection) {
            previewSection.style.display = 'block';
        }

        // 確保隨機排序區域顯示
        const randomSortSection = document.getElementById('randomSortSection');
        if (randomSortSection) {
            randomSortSection.style.display = 'flex';
        }

        // 提取並填充學生姓名到輸入框
        const studentMap = {};
        for (const row of currentSeatingChart) {
            for (const cell of row) {
                if (cell && cell.name) {
                    studentMap[cell.seat_num] = cell.name;
                }
            }
        }
        const sortedSeatNums = Object.keys(studentMap).map(key => parseInt(key)).sort((a, b) => a - b);
        const studentNames = sortedSeatNums.map(seatNum => studentMap[seatNum.toString()]);

        document.getElementById('studentListInput').value = studentNames.join('\n');

        showSuccess('✅ 配置載入成功！版本號：v' + result.version);

    } catch (error) {
        console.error('載入配置失敗：' + error.message);
    }
}

// 啟動自動同步
function startAutoSync() {
    // 每 5 秒檢查一次更新
    if (autoSyncInterval) {
        clearInterval(autoSyncInterval);
    }

    autoSyncInterval = setInterval(async () => {
        try {
            const response = await fetch(
                `/api/check-config-update?current_version=${currentConfigVersion}`
            );

            if (!response.ok) {
                return;
            }

            const result = await response.json();

            if (result.has_update) {
                // 用戶模式下自動同步，管理員模式下詢問
                if (currentUserMode === 'user') {
                    // 用戶模式：自動載入最新配置
                    await loadSavedConfig();
                    showInfo('已自動同步管理員的最新配置');
                } else {
                    // 管理員模式：詢問是否更新
                    if (confirm(`⚠️ 檢測到新版本配置 (v${result.version})\n\n是否要載入最新配置？\n當前未保存的變更將會丟失。`)) {
                        await loadSavedConfig();
                    }
                }
            }

            // 檢查學藝模式是否變化
            if (result.academic_mode !== undefined) {
                const newMode = result.academic_mode ? '學藝' : '一般';
                if (newMode !== currentMode) {
                    currentMode = newMode;
                    updateModeButton();
                    updateModePermissions();
                    showModeInfo();
                }
            }

        } catch (error) {
            console.error('自動同步檢查失敗:', error);
        }
    }, 5000); // 5 秒
}

// 停止自動同步
function stopAutoSync() {
    if (autoSyncInterval) {
        clearInterval(autoSyncInterval);
        autoSyncInterval = null;
    }
}

// 顯示成功提示
function showSuccess(message) {
    // 創建成功提示
    const toast = document.createElement('div');
    toast.className = 'toast-message';
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 15px 25px;
        border-radius: 10px;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.2);
        z-index: 10001;
        animation: slideIn 0.3s ease;
    `;
    toast.textContent = message;

    document.body.appendChild(toast);

    // 3 秒後自動消失
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

// 顯示信息提示
function showInfo(message) {
    const toast = document.createElement('div');
    toast.className = 'toast-message';
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
        color: white;
        padding: 15px 25px;
        border-radius: 10px;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.2);
        z-index: 10001;
        animation: slideIn 0.3s ease;
    `;
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

// 加載不能坐在一起的規則
async function loadCoupleRules() {
    try {
        const response = await fetch('/api/get-couple-rules');
        if (!response.ok) {
            throw new Error('載入座號對規則失敗');
        }

        const result = await response.json();
        coupleRules = result.couples;
        console.log('載入座號對規則成功:', coupleRules);
    } catch (error) {
        console.error('載入座號對規則失敗:', error.message);
    }
}

// 獲取指定座位的所有相鄰座位（包含直接相鄰和隔一個空座位的情況）
function getAdjacentCells(row, col) {
    const adjacent = [];
    // 8個方向的偏移量（直接相鄰）
    const directions = [
        [-1, -1], [-1, 0], [-1, 1],  // 左上、上、右上
        [0, -1],           [0, 1],    // 左、右
        [1, -1],  [1, 0],  [1, 1]     // 左下、下、右下
    ];

    // 檢查直接相鄰（8個方向）
    for (const [dr, dc] of directions) {
        const newRow = row + dr;
        const newCol = col + dc;

        // 檢查是否在有效範圍內
        if (newRow >= 0 && newRow < currentSeatingChart.length &&
            newCol >= 0 && newCol < currentSeatingChart[0].length) {
            const adjacentCell = currentSeatingChart[newRow][newCol];
            if (adjacentCell) {
                adjacent.push({
                    row: newRow,
                    col: newCol,
                    seat_num: adjacentCell.seat_num
                });
            }
        }
    }

    // 檢查「隔一個空座位」的情況（水平和垂直方向）
    const skipDirections = [
        [0, -2],  // 左邊隔一個
        [0, 2],   // 右邊隔一個
        [-2, 0],  // 上邊隔一個
        [2, 0]    // 下邊隔一個
    ];

    for (const [dr, dc] of skipDirections) {
        const newRow = row + dr;
        const newCol = col + dc;

        // 檢查是否在有效範圍內
        if (newRow >= 0 && newRow < currentSeatingChart.length &&
            newCol >= 0 && newCol < currentSeatingChart[0].length) {
            const adjacentCell = currentSeatingChart[newRow][newCol];

            // 檢查中間位置是否為空座位
            const midRow = row + dr / 2;
            const midCol = col + dc / 2;
            const midCell = currentSeatingChart[midRow][midCol];

            // 如果目標位置有座位，且中間位置為空座位
            if (adjacentCell && !midCell) {
                adjacent.push({
                    row: newRow,
                    col: newCol,
                    seat_num: adjacentCell.seat_num
                });
            }
        }
    }

    return adjacent;
}

// 檢查座號對是否在規則列表中
function isCouple(seatNum1, seatNum2) {
    for (const couple of coupleRules) {
        if ((couple[0] === seatNum1 && couple[1] === seatNum2) ||
            (couple[0] === seatNum2 && couple[1] === seatNum1)) {
            return true;
        }
    }
    return false;
}

// 檢查座位表中是否有違規的相鄰座位
function checkAdjacentSeats() {
    const violations = new Set();

    for (let row = 0; row < currentSeatingChart.length; row++) {
        for (let col = 0; col < currentSeatingChart[row].length; col++) {
            const cell = currentSeatingChart[row][col];
            if (!cell) continue;

            const adjacentCells = getAdjacentCells(row, col);

            for (const adjacent of adjacentCells) {
                if (isCouple(cell.seat_num, adjacent.seat_num)) {
                    // 兩個座位都標記為違規
                    violations.add(`${row},${col}`);
                    violations.add(`${adjacent.row},${adjacent.col}`);
                }
            }
        }
    }

    return violations;
}

// 更新警告樣式
function updateWarningStyles() {
    const violations = checkAdjacentSeats();

    for (let row = 0; row < currentSeatingChart.length; row++) {
        for (let col = 0; col < currentSeatingChart[row].length; col++) {
            const cell = currentSeatingChart[row][col];
            if (!cell) continue;

            // 找到對應的 DOM 元素
            const seatCell = document.querySelector(`.seat-cell[data-row="${row}"][data-col="${col}"]`);
            if (seatCell) {
                if (violations.has(`${row},${col}`)) {
                    seatCell.classList.add('warning');
                } else {
                    seatCell.classList.remove('warning');
                }
            }
        }
    }
}

async function loadPresetLayout() {
    const loading = document.getElementById('loading');
    const errorMessage = document.getElementById('errorMessage');
    const randomSortSection = document.getElementById('randomSortSection');
    const previewSection = document.getElementById('previewSection');

    loading.classList.add('active');
    errorMessage.classList.remove('show');

    try {
        const response = await fetch('/api/get-preset-layout');
        if (!response.ok) {
            throw new Error('載入教室配置失敗');
        }

        const result = await response.json();
        currentSeatingChart = result.seating_chart;
        renderSeatingChart(currentSeatingChart);
        previewSection.style.display = 'block';
        randomSortSection.style.display = 'flex';

        // 提取当前座位表中的所有学生姓名，按座號数字顺序
        const studentMap = {};
        for (const row of currentSeatingChart) {
            for (const cell of row) {
                if (cell && cell.name) {
                    studentMap[parseInt(cell.seat_num)] = cell.name;
                }
            }
        }

        // 按座號数字顺序排序
        const sortedSeatNums = Object.keys(studentMap).map(Number).sort((a, b) => a - b);
        const studentNames = sortedSeatNums.map(seatNum => studentMap[seatNum]);

        // 填充到输入框
        document.getElementById('studentListInput').value = studentNames.join('\n');
        randomizedStudentList = [...studentNames];

        // 初始化模式權限
        updateModePermissions();
        showModeInfo();

    } catch (error) {
        showError('載入教室配置失敗，請確認後端服務是否正在運行：' + error.message);
    } finally {
        loading.classList.remove('active');
    }
}

function renderSeatingChart(seatingChart) {
    const grid = document.getElementById('seatingGrid');
    grid.innerHTML = '';

    if (!seatingChart || seatingChart.length === 0) {
        grid.innerHTML = '<p>沒有座位數據</p>';
        return;
    }

    // 計算列數
    const cols = seatingChart[0].length;

    seatingChart.forEach((row, rowIndex) => {
        const rowDiv = document.createElement('div');
        rowDiv.className = 'seat-row';
        rowDiv.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;

        row.forEach((cell, colIndex) => {
            const cellDiv = document.createElement('div');
            if (cell) {
                cellDiv.className = 'seat-cell';
                cellDiv.innerHTML = `
                    <div class="seat-num">${cell.seat_num}</div>
                    <div class="student-name">${cell.name || ''}</div>
                    <div class="seat-coord">(${colIndex}, ${rowIndex})</div>
                `;
                // 添加拖拽属性
                cellDiv.draggable = true;
                cellDiv.dataset.row = rowIndex;
                cellDiv.dataset.col = colIndex;

                // 添加拖拽事件
                cellDiv.addEventListener('dragstart', handleDragStart);
                cellDiv.addEventListener('dragend', handleDragEnd);
                cellDiv.addEventListener('dragover', handleDragOver);
                cellDiv.addEventListener('drop', handleDrop);
                cellDiv.addEventListener('dragenter', handleDragEnter);
                cellDiv.addEventListener('dragleave', handleDragLeave);
            } else {
                cellDiv.className = 'seat-empty';
            }
            rowDiv.appendChild(cellDiv);
        });

        grid.appendChild(rowDiv);
    });

    // 更新警告樣式（檢查不能坐在一起的座位）
    updateWarningStyles();
}

async function generatePDF() {
    // 權限檢查：一般模式無法生成 PDF
    if (currentMode !== '學藝') {
        showError('一般模式無法生成 PDF！請切換到學藝模式後再試。');
        return;
    }

    if (!currentSeatingChart) {
        showError('請先載入教室配置');
        return;
    }

    try {
        const response = await fetch('/api/generate-pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                seating_chart: currentSeatingChart
            })
        });

        if (!response.ok) {
            throw new Error('PDF 生成失敗');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = '座位表.pdf';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

    } catch (error) {
        showError('PDF 生成失敗：' + error.message);
    }
}

function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
    errorMessage.classList.add('show');
}

// 拖拽相关变量
let draggedElement = null;
let draggedRow = null;
let draggedCol = null;

function handleDragStart(e) {
    draggedElement = this;
    draggedRow = parseInt(this.dataset.row);
    draggedCol = parseInt(this.dataset.col);
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
}

function handleDragEnd(e) {
    this.classList.remove('dragging');
    document.querySelectorAll('.seat-cell').forEach(cell => {
        cell.classList.remove('drag-over');
    });
}

function handleDragOver(e) {
    if (e.preventDefault) {
        e.preventDefault();
    }
    e.dataTransfer.dropEffect = 'move';
    return false;
}

function handleDragEnter(e) {
    if (this !== draggedElement) {
        this.classList.add('drag-over');
    }
}

function handleDragLeave(e) {
    this.classList.remove('drag-over');
}

function handleDrop(e) {
    if (e.stopPropagation) {
        e.stopPropagation();
    }

    if (draggedElement !== this) {
        const targetRow = parseInt(this.dataset.row);
        const targetCol = parseInt(this.dataset.col);

        // 同时交换座号和姓名，保持座号与姓名的对应关系
        const tempSeatNum = currentSeatingChart[targetRow][targetCol].seat_num;
        const tempName = currentSeatingChart[targetRow][targetCol].name;

        currentSeatingChart[targetRow][targetCol].seat_num = currentSeatingChart[draggedRow][draggedCol].seat_num;
        currentSeatingChart[targetRow][targetCol].name = currentSeatingChart[draggedRow][draggedCol].name;

        currentSeatingChart[draggedRow][draggedCol].seat_num = tempSeatNum;
        currentSeatingChart[draggedRow][draggedCol].name = tempName;

        // 重新渲染
        renderSeatingChart(currentSeatingChart);

        // 管理員模式：重新渲染後自動保存，用戶模式：不保存
        scheduleAutoSave();
    }

    return false;
}

// 隨機排序相關函數
let randomizedStudentList = [];

function randomizeStudentList() {
    const textarea = document.getElementById('studentListInput');
    const lines = textarea.value.split('\n').filter(line => line.trim() !== '');

    if (lines.length === 0) {
        showError('請先輸入學生姓名');
        return;
    }

    // Fisher-Yates 隨機洗牌算法
    for (let i = lines.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [lines[i], lines[j]] = [lines[j], lines[i]];
    }

    randomizedStudentList = lines;
    textarea.value = lines.join('\n');
}

function applyRandomizedList() {
    if (!currentSeatingChart) {
        showError('請先載入教室配置');
        return;
    }

    // 收集所有座號和对应的姓名（保持对应关系）
    const seatData = [];
    for (let row = 0; row < currentSeatingChart.length; row++) {
        for (let col = 0; col < currentSeatingChart[row].length; col++) {
            if (currentSeatingChart[row][col]) {
                seatData.push({
                    seat_num: currentSeatingChart[row][col].seat_num,
                    name: currentSeatingChart[row][col].name
                });
            }
        }
    }

    // 隨机打乱座號顺序（但保持座號和姓名的对应关系）
    for (let i = seatData.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [seatData[i], seatData[j]] = [seatData[j], seatData[i]];
    }

    // 按空间位置顺序（从左到右，从上到下）分配座號和姓名
    let dataIndex = 0;
    for (let row = 0; row < currentSeatingChart.length; row++) {
        for (let col = 0; col < currentSeatingChart[row].length; col++) {
            if (currentSeatingChart[row][col] && dataIndex < seatData.length) {
                currentSeatingChart[row][col].seat_num = seatData[dataIndex].seat_num;
                currentSeatingChart[row][col].name = seatData[dataIndex].name;
                dataIndex++;
            }
        }
    }

    // 重新渲染座位表
    renderSeatingChart(currentSeatingChart);
    alert('✅ 已將座號隨機分配到座位（座號與姓名對應關係保持不變）！');
}

function fillFromPosition() {
    if (!currentSeatingChart) {
        showError('請先載入教室配置');
        return;
    }

    // 检查是否已随机化学生列表
    if (randomizedStudentList.length === 0) {
        showError('請先點擊「🎲 隨機化」按鈕來生成隨機序列！');
        return;
    }

    // 获取起始位置
    const startRow = parseInt(document.getElementById('startRow').value);
    const startCol = parseInt(document.getElementById('startCol').value);

    // 验证坐标范围
    if (startRow < 0 || startRow >= currentSeatingChart.length) {
        showError(`起始行超出範圍！請輸入 0 到 ${currentSeatingChart.length - 1} 之間的數值`);
        return;
    }
    if (startCol < 0 || startCol >= currentSeatingChart[0].length) {
        showError(`起始列超出範圍！請輸入 0 到 ${currentSeatingChart[0].length - 1} 之間的數值`);
        return;
    }

    // 检查起始位置是否有座位
    if (!currentSeatingChart[startRow][startCol]) {
        showError(`起始位置 (${startCol}, ${startRow}) 沒有座位！請選擇一個有效的座位位置`);
        return;
    }

    // 收集所有座號和对应的姓名（保持对应关系）
    const seatData = [];
    for (let row = 0; row < currentSeatingChart.length; row++) {
        for (let col = 0; col < currentSeatingChart[row].length; col++) {
            if (currentSeatingChart[row][col]) {
                seatData.push({
                    seat_num: currentSeatingChart[row][col].seat_num,
                    name: currentSeatingChart[row][col].name
                });
            }
        }
    }

    // 根据 randomizedStudentList 中姓名的出现顺序，重新排列（座號, 姓名）对
    // 座號和姓名的对应关系保持不变
    const orderedSeatData = [];
    for (const name of randomizedStudentList) {
        // 找到匹配的座號-姓名对
        const found = seatData.find(item => item.name === name);
        if (found) {
            orderedSeatData.push(found);
            // 从原数组中移除已使用的对
            const index = seatData.indexOf(found);
            seatData.splice(index, 1);
        }
    }

    // 如果 randomizedStudentList 中有未匹配的姓名，把剩余的（座號, 姓名）对也加进去
    for (const item of seatData) {
        orderedSeatData.push(item);
    }

    // 从指定位置开始，按列优先填充（向下填完一列，再向右移到下一列）
    // 如果填到右下角還沒填完，回到起始列从第0行继续填
    let dataIndex = 0;
    const totalRows = currentSeatingChart.length;
    const totalCols = currentSeatingChart[0].length;
    const visited = new Set();

    let currentCol = startCol;
    let currentRow = startRow;
    let isWrapping = false;
    let iterations = 0;
    const maxIterations = totalRows * totalCols * 2; // 安全限制，防止无限循环

    while (dataIndex < orderedSeatData.length && iterations < maxIterations) {
        iterations++;
        const key = `${currentRow},${currentCol}`;

        // 如果当前位置有座位且未被填充过
        if (currentSeatingChart[currentRow][currentCol] && !visited.has(key)) {
            currentSeatingChart[currentRow][currentCol].seat_num = orderedSeatData[dataIndex].seat_num;
            currentSeatingChart[currentRow][currentCol].name = orderedSeatData[dataIndex].name;
            visited.add(key);
            dataIndex++;
        }

        // 移动到下一个位置（向下）
        if (currentRow < totalRows - 1) {
            currentRow++;
        } else {
            // 当前列已填完，移动到下一列
            currentCol++;
            currentRow = 0;

            // 如果超出所有列，回到起始列
            if (currentCol >= totalCols) {
                currentCol = 0;
                isWrapping = true;
            }

            // 如果回到起始列且已经绕过一次，说明已经检查完所有位置
            if (isWrapping && currentCol > startCol) {
                break;
            }
        }
    }

    // 重新渲染座位表
    renderSeatingChart(currentSeatingChart);
    alert(`✅ 已從位置 (${startCol}, ${startRow}) 開始按列優先填充座號（根據隨機序列順序，座號與姓名對應關係保持不變）！`);

    // 重新渲染後自動保存
    saveCurrentConfig();
}

function toggleFullscreen() {
    const previewSection = document.getElementById('previewSection');
    const fullscreenBtn = document.getElementById('fullscreenBtn');

    if (document.fullscreenElement) {
        document.exitFullscreen();
        previewSection.classList.remove('fullscreen');
        fullscreenBtn.textContent = '🖥️ 全螢幕';
    } else {
        previewSection.requestFullscreen().then(() => {
            previewSection.classList.add('fullscreen');
            fullscreenBtn.textContent = '📵 退出全螢幕';
        }).catch(err => {
            showError('無法進入全螢幕模式：' + err.message);
        });
    }
}

// 监听全屏变化事件
document.addEventListener('fullscreenchange', () => {
    const previewSection = document.getElementById('previewSection');
    const fullscreenBtn = document.getElementById('fullscreenBtn');

    if (!document.fullscreenElement) {
        previewSection.classList.remove('fullscreen');
        fullscreenBtn.textContent = '🖥️ 全螢幕';
    }
});

// 右鍵菜單功能初始化
document.addEventListener('DOMContentLoaded', function() {
    const previewSection = document.getElementById('previewSection');
    const contextMenu = document.getElementById('contextMenu');

    // 右鍵菜單事件
    previewSection.addEventListener('contextmenu', function(e) {
        e.preventDefault();
        showContextMenu(e.clientX, e.clientY);
    });

    // 點擊其他地方關閉菜單
document.addEventListener('click', function(e) {
        if (!contextMenu.contains(e.target)) {
            hideContextMenu();
        }
    });

    // 按鍵關閉菜單（ESC）
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            hideContextMenu();
        }
    });

    // 窗口滾動時關閉菜單
    window.addEventListener('scroll', function() {
        hideContextMenu();
    });
});