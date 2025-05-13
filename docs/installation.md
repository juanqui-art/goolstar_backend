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
```

## Despliegue en Supabase

El proyecto está actualmente desplegado en Supabase, que proporciona la infraestructura para la base de datos PostgreSQL y servicios adicionales.

### Acceso a la base de datos

- **Host:** db.supabase.co
- **Puerto:** 5432
- **Base de datos:** goolstar_db

### Configuración para desarrollo

Para conectar tu entorno de desarrollo local con la base de datos de Supabase:

1. Configura las variables de entorno en un archivo `.env`:

```
DATABASE_URL=postgresql://usuario:contraseña@db.supabase.co:5432/goolstar_db
SUPABASE_KEY=tu_clave_api
```

2. Actualiza tu configuración de Django para usar estas variables.

### Servicios utilizados

- **Base de datos PostgreSQL**: Almacenamiento principal
- **Autenticación**: Gestión de usuarios y sesiones
- **Storage**: Almacenamiento de archivos (fotos de jugadores, logos de equipos)