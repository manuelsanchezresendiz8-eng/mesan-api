FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m mesanuser
USER mesanuser

COPY --chown=mesanuser:mesanuser requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=mesanuser:mesanuser . .

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
