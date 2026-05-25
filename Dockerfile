FROM python:3.11-slim

WORKDIR /app

# ============================================
# SYSTEM DEPENDENCIES
# ============================================

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# CREATE NON-ROOT USER
# ============================================

RUN useradd -m mesanuser

# ============================================
# ENVIRONMENT
# ============================================

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PATH=/home/mesanuser/.local/bin:$PATH

# ============================================
# INSTALL REQUIREMENTS
# ============================================

COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================
# COPY PROJECT
# ============================================

COPY . .

# ============================================
# PERMISSIONS
# ============================================

RUN chown -R mesanuser:mesanuser /app

USER mesanuser

# ============================================
# RENDER PORT
# ============================================

EXPOSE 10000

# ============================================
# HEALTHCHECK
# ============================================

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
CMD curl --fail http://localhost:${PORT:-10000}/health || exit 1

# ============================================
# START
# ============================================

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
