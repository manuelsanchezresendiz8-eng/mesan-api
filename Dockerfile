# ============================================
# MESAN Ω Dockerfile v1.1
# Enterprise Runtime
# ============================================

FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN useradd -m mesanuser

# Python env
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PATH=/home/mesanuser/.local/bin:$PATH

# Install deps first (cache layer)
COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt

# Copy app
COPY . .

# Permissions
RUN chown -R mesanuser:mesanuser /app

USER mesanuser

# Render uses 10000 internally
EXPOSE 10000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl --fail http://localhost:10000/health || exit 1

# Runtime
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
