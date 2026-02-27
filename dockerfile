FROM python:3.9-slim

# 修正：刪除不存在的 xelatex 套件名稱，只保留正確的編譯引擎與字體
RUN apt-get update && apt-get install -y \
    texlive-xetex \
    texlive-lang-chinese \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 更新字體快取
RUN fc-cache -fv

WORKDIR /app
COPY . .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

ENV PORT=8080
EXPOSE 8080

# 啟動命令
CMD ["gunicorn", "server:app", "--bind", "0.0.0.0:8080", "--timeout", "120"]

