FROM python:3.9-slim

# 安裝 XeLaTeX 必要的 Linux 系統組件
RUN apt-get update && apt-get install -y \
    xelatex \
    texlive-xetex \
    texlive-lang-chinese \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 設定連接埠
ENV PORT=8080
EXPOSE 8080

# 啟動命令
CMD ["gunicorn", "server:app", "--bind", "0.0.0.0:8080", "--timeout", "120"]
