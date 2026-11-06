FROM python:3.11-slim

WORKDIR /app

# System dependencies for PDF extraction + ML
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    tesseract-ocr \
    poppler-utils \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ml/ ./ml/
COPY data/ ./data/

CMD ["python", "-m", "ml.training.train_cost_model"]
