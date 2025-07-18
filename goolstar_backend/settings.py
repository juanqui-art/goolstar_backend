"""
Django settings for GoolStarProject project.

Generated by 'django-admin startproject' using Django 5.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path

from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
import os

SECRET_KEY = os.environ.get('SECRET_KEY')
if SECRET_KEY is None:
    if os.environ.get('PRODUCTION', 'False') == 'True':
        raise ValueError(
            "ERROR: No SECRET_KEY definida en variables de entorno. "
            "Esto es obligatorio para entornos de producción."
        )
    else:
        # Solo para desarrollo, nunca debe usarse en producción
        SECRET_KEY = 'django-insecure-t03zw!p1mo32-9&d_z&%&fltgm!=td5qn$4piq%n!+zj&tbx%$'

# SECURITY WARNING: don't run with debug turned on in production!
# TEMPORALMENTE ACTIVADO PARA DEBUGGING - REVERTIR DESPUÉS
DEBUG = False  # ⚠️ TEMPORAL: Activado para diagnóstico del error 500
# DEBUG = False
# if os.environ.get('PRODUCTION', 'False') != 'True':
#     # Solo habilitar DEBUG si estamos en desarrollo y se especifica explícitamente
#     DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.fly.dev']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_filters',  # Nombre corregido: con guión bajo, no con guión
    # Apps instaladas
    'rest_framework',
    'rest_framework.authtoken',  # Para autenticación basada en tokens
    'corsheaders',
    'rest_framework_simplejwt',  # Para autenticación con JWT
    'rest_framework_simplejwt.token_blacklist',  # Añadido para permitir blacklist de tokens
    'drf_spectacular',
    # Cloudinary para almacenamiento de documentos
    'cloudinary_storage',
    'cloudinary',
    # Apps locales
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Para archivos estáticos en producción
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'api.middleware.logging_middleware.RequestLoggingMiddleware',  # Middleware para logging HTTP
]

# Agregar middleware de performance solo en desarrollo
if DEBUG:
    MIDDLEWARE.insert(0, 'api.middleware.performance_middleware.PerformanceMiddleware')

# Configuración de CORS
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',  # Para desarrollo local con Next.js
    'https://goolstar.vercel.app',  # Frontend en Vercel principal
    'https://goolstar-juanquiarts-projects.vercel.app',  # Frontend en Vercel secundario
    'https://goolstar-697hki8h0-juanquiarts-projects.vercel.app',  # Frontend en Vercel preview
    'https://goolstar-backend.fly.dev',  # Backend en Fly.io
]

# Configuración de seguridad para producción
if not DEBUG:
    # SSL redirect habilitado para seguridad (Fly.io ya maneja esto con force_https)
    SECURE_SSL_REDIRECT = False  # Fly.io maneja esto automáticamente
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Headers básicos de seguridad
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    X_FRAME_OPTIONS = 'DENY'

# Configuración de CSRF para Fly.io
CSRF_TRUSTED_ORIGINS = [
    'https://goolstar-backend.fly.dev',
    'https://goolstar.vercel.app',
    'https://goolstar-juanquiarts-projects.vercel.app',
    'https://goolstar-697hki8h0-juanquiarts-projects.vercel.app',
    'http://localhost:8000',
]

ROOT_URLCONF = 'goolstar_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR / 'api' / 'templates',  # Añadir el directorio de plantillas de api
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'goolstar_backend.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

import dj_database_url

# Configuración por defecto (SQLite para desarrollo)
if 'DATABASE_URL' in os.environ:
    # Configuración para producción con PostgreSQL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DATABASE_NAME', 'postgres'),
            'USER': os.environ.get('DATABASE_USER', 'postgres'),
            'PASSWORD': os.environ.get('DATABASE_PASSWORD', ''),
            'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
            'PORT': os.environ.get('DATABASE_PORT', '5432'),
            'CONN_MAX_AGE': 120,  # Reducido de 600 a 60 segundos
        }
    }

    # También intentamos parsear DATABASE_URL si está presente
    db_from_env = dj_database_url.config(conn_max_age=60)
    if db_from_env:
        DATABASES['default'].update(db_from_env)
else:
    # Configuración para desarrollo
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db_local.sqlite3',
        }
    }

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Configuración de Whitenoise para compresión y caché
WHITENOISE_MIDDLEWARE_WHITELIST = ['/static/', '/media/']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (Uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Configuración de Cloudinary para documentos de jugadores
import cloudinary.api

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
    'SECURE': True,  # Usar HTTPS
    'FOLDER': 'goolstar_documentos',  # Carpeta específica para documentos
}

# Configurar Cloudinary con las credenciales
cloudinary.config(
    cloud_name=CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=CLOUDINARY_STORAGE['API_KEY'],
    api_secret=CLOUDINARY_STORAGE['API_SECRET'],
    secure=CLOUDINARY_STORAGE['SECURE']
)

# Configuración de seguridad para subida de archivos
CLOUDINARY_ALLOWED_FORMATS = ['jpg', 'jpeg', 'png', 'pdf']
CLOUDINARY_MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB máximo por archivo
CLOUDINARY_RESOURCE_TYPE = 'auto'  # Auto-detectar tipo de recurso

# Configuración de Logging
LOGS_DIR = BASE_DIR / 'logs'

# Configuración de logging para desarrollo y producción
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} [{levelname}] {name} {filename}:{lineno:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file_debug': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'debug.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'file_info': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'info.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'error.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose',
        },
        'timezone_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'timezone.log',
            'maxBytes': 5 * 1024 * 1024,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_info', 'mail_admins'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.server': {
            'handlers': ['console', 'file_info'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['file_error', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['file_debug'] if DEBUG else [],
            'level': 'DEBUG',
            'propagate': False,
        },
        # Loggers personalizados para nuestra aplicación
        'api': {
            'handlers': ['console', 'file_info', 'file_error'],
            'level': 'DEBUG',
            'propagate': True,
        },
        # Logger específico para documentos de jugadores y Cloudinary
        'api.models.participantes': {
            'handlers': ['console', 'file_debug', 'file_error'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'cloudinary': {
            'handlers': ['console', 'file_debug', 'file_error'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'api.middleware.logging': {
            'handlers': ['console', 'file_info', 'file_error'],
            'level': 'INFO',
            'propagate': False,
        },
        'api.utils.tz_logging': {
            'handlers': ['console', 'timezone_file', 'file_error'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'goolstar_backend': {
            'handlers': ['console', 'file_info', 'file_error'],
            'level': 'DEBUG',
            'propagate': True,
        },
        # Añadir loggers específicos para módulos con zona horaria
        '*.timezone': {
            'handlers': ['timezone_file', 'file_error'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Añadir a .env.example
# EMAIL_HOST=smtp.example.com
# EMAIL_PORT=587
# EMAIL_HOST_USER=your_email@example.com
# EMAIL_HOST_PASSWORD=your_password
# EMAIL_USE_TLS=True
# DEFAULT_FROM_EMAIL=your_email@example.com
# ADMINS=[('Admin Name', 'admin@example.com')]

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 30,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # Rate limiting (throttling) configuration
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/hour',  # ✅ Aumentado de 100 a 1000
        'user': '5000/hour',  # ✅ Aumentado de 1000 a 5000
        'login': '20/min',  # ✅ Aumentado de 5 a 20
        'register': '10/min',  # ✅ Aumentado de 3 a 10
    }
}
SPECTACULAR_SETTINGS = {
    'TITLE': 'GoolStar API',
    'DESCRIPTION': 'API para gestión de competiciones deportivas',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # Configuraciones específicas para tu API
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
}
# Simple JWT settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),  # Token de acceso válido por 1 hora
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),  # Token de refresco válido por 7 días
    'ROTATE_REFRESH_TOKENS': True,  # Genera un nuevo refresh token cuando se usa
    'BLACKLIST_AFTER_ROTATION': True,  # Agregado para permitir blacklist de tokens

    'ALGORITHM': 'HS256',  # Algoritmo de firma (HMAC con SHA-256)
    'SIGNING_KEY': SECRET_KEY,  # Usa la clave secreta de Django para firmar
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),  # Tipo de cabecera de autenticación (Bearer token)
    'USER_ID_FIELD': 'id',  # Campo que identifica al usuario
    'USER_ID_CLAIM': 'user_id',  # Nombre del claim en el token
}

import sys

if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

# Deshabilitar redirección automática para barras diagonales finales
APPEND_SLASH = True

# Redis Cache Configuration (opcional - fallback a LocMemCache si no está disponible)
REDIS_URL = os.environ.get('REDIS_URL')

if REDIS_URL:
    # Usar Redis si está configurado
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 20,
                    'retry_on_timeout': True,
                },
                'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
                'IGNORE_EXCEPTIONS': True,  # No fallar si Redis no está disponible
            },
            'KEY_PREFIX': 'goolstar',
            'TIMEOUT': 300,  # 5 minutos por defecto
        }
    }
else:
    # Fallback a cache en memoria local si Redis no está configurado
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'goolstar-cache',
            'TIMEOUT': 300,
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
                'CULL_FREQUENCY': 3,
            }
        }
    }

# Configuración específica de cache
CACHE_TTL = {
    'tabla_posiciones': 300,  # 5 minutos - se actualiza frecuentemente
    'estadisticas_equipo': 600,  # 10 minutos 
    'partidos_proximos': 180,  # 3 minutos - información crítica
    'equipos_categoria': 1800,  # 30 minutos - cambia poco
    'jugadores_equipo': 900,  # 15 minutos
    'torneo_detalle': 3600,  # 1 hora - información estable
}
