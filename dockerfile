FROM python:3.9-slim

# 只安裝基本字型套件，不再安裝幾 GB 的 TeX Live
RUN apt-get update && apt-get install -y \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

ENV PORT=8080
EXPOSE 8080

CMD ["gunicorn", "server:app", "--bind", "0.0.0.0:8080"]
