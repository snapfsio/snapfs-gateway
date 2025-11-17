FROM python:3.12-slim

# Fast startup, clean logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy the app
COPY gateway.py /app/gateway.py

# OS deps (curl only for HEALTHCHECK; remove if you don't use it)
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

# Python deps:
# - fastapi + uvicorn[standard] → websockets + httptools
# - nats-py → NATS/JetStream client
# - redis → Redis (L2)
# - aiomysql → MySQL fallback (L3)
RUN pip install --no-cache-dir \
      cryptography \
      fastapi "uvicorn[standard]" \
      nats-py \
      redis \
      aiomysql

# Sensible defaults; override via docker compose or `docker run -e ...`
ENV NATS_URL="nats://nats:4222" \
    SNAPFS_STREAM="SNAPFS_FILES" \
    SNAPFS_SUBJECT="snapfs.files" \
    L2_BACKEND="redis" \
    REDIS_URL="redis://redis:6379/0" \
    SQL_FALLBACK="on" \
    MYSQL_URL="mysql://snapfs:snapfs@mysql:3306/snapfs"

EXPOSE 8000

# Optional: basic container-level healthcheck
# (If you added a /healthz route, point to that; /docs is fine for PoC.)
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=10 \
  CMD curl -fsS http://127.0.0.1:8000/docs >/dev/null || exit 1

CMD ["uvicorn", "gateway:app", "--host", "0.0.0.0", "--port", "8000"]
