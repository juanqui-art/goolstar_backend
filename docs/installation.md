# Instalación del Sistema

## Requisitos previos
- Python 3.8+
- Django 4.2+
- PostgreSQL (recomendado)

## Instalación paso a paso
```bash
# 1. Clonar repositorio
git clone ...

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar base de datos
python manage.py migrate

# 5. Crear superusuario
python manage.py createsuperuser