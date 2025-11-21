FROM python:3.12-slim

# Fast startup, clean logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (curl only for HEALTHCHECK)
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md LICENSE /app/
COPY src /app/src

# Install gateway package + runtime deps via pyproject.toml
RUN pip install --no-cache-dir .

# Runtime configuration (override in compose/k8s)
ENV SNAPFS_ENV="prod" \
    MYSQL_URL="mysql+pymysql://snapfs:snapfs@localhost:3306/snapfs" \
    REDIS_URL="redis://redis:6379/0" \
    NATS_URL="nats://nats:4222"

EXPOSE 8000

# Healthcheck hits the /healthz endpoint we defined in main.py
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=10 \
  CMD curl -fsS http://127.0.0.1:8000/healthz >/dev/null || exit 1

# Run the FastAPI app via uvicorn
CMD ["uvicorn", "snapfs_gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
