# 使用官方 Python 3.9 輕量映像檔
FROM python:3.9-slim

# 安裝 XeLaTeX 引擎與中文字包
# fonts-noto-cjk 是 Linux 上最穩定的中文字體
RUN apt-get update && apt-get install -y \
    xelatex \
    texlive-xetex \
    texlive-lang-chinese \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 更新字體快取
RUN fc-cache -fv

# 設定工作目錄
WORKDIR /app

# 複製程式碼與依賴檔
COPY . .

# 安裝 Python 套件
RUN pip install --no-cache-dir -r requirements.txt

# Railway 預設 PORT 為 8080
ENV PORT=8080
EXPOSE 8080

# 啟動伺服器
CMD ["gunicorn", "server:app", "--bind", "0.0.0.0:8080"]
