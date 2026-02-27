# 使用輕量級 Python 映像檔
FROM python:3.9-slim

# 安裝 XeLaTeX 及其相關組件 (最小化安裝以節省空間)
RUN apt-get update && apt-get install -y \
    texlive-xetex \
    texlive-lang-chinese \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 設定工作目錄
WORKDIR /app
COPY . .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 啟動伺服器
CMD ["gunicorn", "server:app", "--bind", "0.0.0.0:8080"]