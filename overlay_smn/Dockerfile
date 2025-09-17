# syntax=docker/dockerfile:1
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      tzdata ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

ENV TZ=America/Argentina/Buenos_Aires \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UVICORN_WORKERS=2 \
    UVICORN_PORT=8000

# Creamos usuario y directorios
RUN useradd -ms /bin/bash appuser
WORKDIR /srv/overlay-smn
RUN mkdir -p /srv/overlay-smn/data/raw /srv/overlay-smn/data/parsed

# Deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Código
COPY . .
RUN chown -R appuser:appuser /srv/overlay-smn

# --- start.sh como root y luego bajamos privilegios ---
COPY start.sh /usr/local/bin/start.sh
RUN chmod 0755 /usr/local/bin/start.sh

# Ahora sí, usuario no-root
USER appuser

EXPOSE 8000

# Healthcheck (requiere /health en FastAPI)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:${UVICORN_PORT}/health || exit 1

CMD ["start.sh"]

