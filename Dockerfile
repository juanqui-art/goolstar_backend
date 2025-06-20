FROM python:3.12-slim

# Metadata labels
LABEL maintainer="GoolStar Team"
LABEL version="1.0"
LABEL description="GoolStar Tournament Management API - Django 5.2 + DRF"
LABEL org.opencontainers.image.source="https://github.com/user/goolstar"

WORKDIR /app

# Configurar variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=False
# Asegurarnos de que Fly.io reconozca esta variable
ENV PORT=8000

# Configuración Gunicorn optimizada para Fly.io (1 CPU + 2GB RAM)
ENV GUNICORN_WORKERS=3
ENV GUNICORN_WORKER_CLASS=gthread
ENV GUNICORN_THREADS=2
ENV GUNICORN_TIMEOUT=60
ENV GUNICORN_KEEPALIVE=5
ENV GUNICORN_MAX_REQUESTS=800
ENV GUNICORN_MAX_REQUESTS_JITTER=50

# Instalar dependencias del sistema necesarias para python-magic
RUN apt-get update && apt-get install -y \
    libmagic1 \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

# Actualizar pip y instalar dependencias de Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el proyecto
COPY . .

# Crear directorio de logs necesario para Django logging
RUN mkdir -p /app/logs

# Recolectar archivos estáticos
RUN python manage.py collectstatic --noinput

# Exponer el puerto - esto es muy importante para Fly.io
EXPOSE ${PORT}

# Health check básico para monitoreo
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python manage.py check --deploy || exit 1

# Ejecutar servidor con configuración optimizada para Fly.io
CMD ["sh", "-c", "exec gunicorn goolstar_backend.wsgi:application --bind=0.0.0.0:8000 --workers=${GUNICORN_WORKERS:-3} --worker-class=${GUNICORN_WORKER_CLASS:-gthread} --threads=${GUNICORN_THREADS:-2} --timeout=${GUNICORN_TIMEOUT:-60} --keep-alive=${GUNICORN_KEEPALIVE:-5} --max-requests=${GUNICORN_MAX_REQUESTS:-800} --max-requests-jitter=${GUNICORN_MAX_REQUESTS_JITTER:-50} --access-logfile=- --error-logfile=-"]
