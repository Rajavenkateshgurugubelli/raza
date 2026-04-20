# ── R.A.Z.A. Backend Dockerfile ──────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# System deps for sentence-transformers + faster-whisper + av
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgomp1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Data directories that will be mounted as volumes
RUN mkdir -p /app/data/chroma_db

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
