FROM python:3.10-slim

# install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# non-root user — created before COPY so chown works in one layer
RUN adduser --disabled-password --gecos "" appuser

# set the working directory
WORKDIR /app

# copy app files owned by appuser so the process can read/write tmp files
COPY --chown=appuser:appuser . /app

# install deps as root (writes to system Python path, readable by all users)
RUN pip install --no-cache-dir -r requirements.txt

# drop to non-root for runtime
USER appuser

# expose the port
EXPOSE 8000

# run the app — gunicorn process manager with uvicorn workers
# WORKERS default: 4; override at runtime with -e WORKERS=N
CMD ["sh", "-c", "gunicorn teramina.asgi:application -k uvicorn.workers.UvicornWorker -w ${WORKERS:-4} --bind 0.0.0.0:${PORT:-8000} --timeout 120 --graceful-timeout 30 --access-logfile - --error-logfile -"]
