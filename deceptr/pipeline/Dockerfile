FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libmaxminddb-dev libmaxminddb0 curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/data

RUN useradd -r -u 1001 -g root deceptr && chown -R deceptr:root /app
USER deceptr

# Default : pipeline. Overridable avec `command:` dans docker-compose
CMD ["python", "main.py"]
