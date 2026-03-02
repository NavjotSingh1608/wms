# WMS Backend — FastAPI + Celery
FROM python:3.12-slim

WORKDIR /app

# libpq-dev needed for psycopg2-binary on slim images
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default: run API (overridden in docker-compose for worker/beat)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
