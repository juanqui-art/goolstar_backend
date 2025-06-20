FROM python:3.11-slim

WORKDIR /app

# Configurar variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=False
# Asegurarnos de que Fly.io reconozca esta variable
ENV PORT=8000

# Instalar dependencias del sistema necesarias para python-magic
RUN apt-get update && apt-get install -y \
    libmagic1 \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el proyecto
COPY . .

# Crear directorio de logs necesario para Django logging
RUN mkdir -p /app/logs

# Recolectar archivos estáticos
RUN python manage.py collectstatic --noinput

# Exponer el puerto - esto es muy importante para Fly.io
EXPOSE ${PORT}

# Ejecutar servidor sin migraciones por ahora para evitar problemas de conexión DB
CMD ["gunicorn", "goolstar_backend.wsgi:application", "--bind", "0.0.0.0:8000"]
