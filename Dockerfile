FROM python:3.11-slim

WORKDIR /app

# Configurar variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=False

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el proyecto
COPY . .

# Recolectar archivos estáticos
RUN python manage.py collectstatic --noinput

# Ejecutar migraciones y servidor
CMD ["sh", "-c", "python manage.py migrate && gunicorn goolstar_backend.wsgi:application --bind 0.0.0.0:8000"]

EXPOSE 8000
