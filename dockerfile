# 使用 Python 3.9 輕量版
FROM python:3.9-slim

# 安裝 XeLaTeX 及其所需的中文字體與組件
# 這會讓環境支援執行 'xelatex' 指令
RUN apt-get update && apt-get install -y \
    xelatex \
    texlive-xetex \
    texlive-lang-chinese \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 設定工作目錄
WORKDIR /app

# 複製所有檔案到容器中
COPY . .

# 安裝 Python 依賴（包含 Gunicorn）
RUN pip install --no-cache-dir -r requirements.txt

# 設定環境變數與連接埠
ENV PORT=8080
EXPOSE 8080

# 使用 Gunicorn 啟動伺服器
CMD ["gunicorn", "server:app", "--bind", "0.0.0.0:8080"]
