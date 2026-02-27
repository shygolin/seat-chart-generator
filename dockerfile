FROM python:3.9-slim

# 安裝基本字型套件 (作為備援)
RUN apt-get update && apt-get install -y \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

ENV PORT=8080
EXPOSE 8080

CMD ["gunicorn", "server:app", "--bind", "0.0.0.0:8080"]

