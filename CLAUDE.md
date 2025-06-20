# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- **Run server**: `python manage.py runserver`
- **Run tests**: `python manage.py test`
- **Run single test**: `python manage.py test api.tests.TestClassName.test_method_name`
- **Create migrations**: `python manage.py makemigrations`
- **Apply migrations**: `python manage.py migrate`
- **Cache management**: `python manage.py cache_management --action test|stats|clear`
- **Lint code**: `flake8`
- **Check types**: `mypy .`

## Dependencies Management

- **Production install**: `pip install -r requirements.txt`
- **Development install**: `pip install -r requirements.txt -r requirements-dev.txt`
- **Security audit**: `pip-audit` (dev only)
- **Dependency tree**: `pipdeptree` (dev only)

## Architecture Overview

### Project Structure
This is a **Django 5.2 + Django REST Framework** sports tournament management system with enterprise-level optimizations:

- **Core App**: `api/` contains all business logic organized by domain
- **Models**: Modular design in `api/models/` (participantes, competicion, estadisticas, financiero)
- **Views**: Domain-specific ViewSets in `api/views/` with comprehensive caching and optimization
- **Serializers**: Multiple variants per model (`List`, `Detail`, `Base`) for performance
- **Services**: Business logic layer in `api/services/` for complex operations

### Performance Architecture
The system implements **production-grade performance optimizations**:

- **Query Optimization**: Extensive use of `select_related`/`prefetch_related` reducing DB queries by 80-90%
- **Hybrid Cache System**: Redis in production with LocMemCache fallback (no Redis dependency required)
- **Intelligent Serialization**: Context-aware serializers (list vs detail views)
- **Database Indexes**: Strategic indexes on high-traffic queries
- **Cursor Pagination**: Eliminates expensive COUNT queries for large datasets

### Security Features
- **Rate Limiting**: Granular throttling (login: 5/min, register: 3/min, API: 5000/hour)
- **JWT Authentication**: Access/refresh tokens with blacklisting support
- **CORS/CSRF Protection**: Configured for frontend integration
- **Security Headers**: HSTS, XSS protection, content type sniffing prevention

### Key Endpoints
- **Tournament Management**: `/api/torneos/` with custom actions (tabla_posiciones, estadisticas)
- **Team Management**: `/api/equipos/` with category filtering and caching
- **Player Management**: `/api/jugadores/` with document upload via Cloudinary
- **Match Management**: `/api/partidos/` with goals and cards tracking
- **Authentication**: JWT-based with `/api/auth/` endpoints

## Code Style Guidelines

- **Imports**: Group imports in this order: standard library, Django/DRF, third-party packages, local apps
- **Formatting**: Follow PEP 8 conventions with 4-space indentation
- **Models**: Define `__str__` methods and Meta classes as needed; add docstrings for model classes
- **Validation**: Use Django's clean/validation methods and model validators
- **Error Handling**: Use Django exceptions (ValidationError, PermissionDenied) appropriately
- **Naming**: Use lowercase with underscores for variables/functions; CamelCase for classes
- **Documentation**: Add docstrings to models, views, and complex functions
- **Security**: Never hardcode secrets; use environment variables loaded via python-dotenv

## Performance Guidelines

- **Always use optimized querysets** in ViewSets with `select_related`/`prefetch_related`
- **Leverage the cache system** using `@cached_view_result` decorator for expensive operations
- **Use appropriate serializers** (List for listings, Detail for individual resources)
- **Implement pagination** using the custom `OptimizedCursorPagination` for large datasets
- **Add indexes** for new query patterns following existing patterns in migrations

## Deployment Configuration

- **Environment**: Uses `.env` for local development, environment variables for production
- **Database**: PostgreSQL in production (Supabase), SQLite for development
- **Static Files**: WhiteNoise with compression and manifest-based caching
- **File Uploads**: Cloudinary integration for player documents
- **Server**: ASGI-ready (can run async views) but currently uses WSGI
- **Monitoring**: Comprehensive logging system with rotating files and performance tracking

## Performance Status

✅ **PRODUCTION-READY OPTIMIZATIONS**:
- Query Optimization: 80-90% fewer DB queries via select_related/prefetch_related
- Hybrid Cache System: Redis/LocMemCache with automatic invalidation
- Database Indexes: Strategic indexes reducing search time by 50-80%
- Serializer Optimization: Context-aware serializers reducing response time 20-40%
- Cursor Pagination: Eliminates COUNT queries for better performance on large datasets
- Security: Rate limiting, SSL headers, CSRF/CORS protection
- Monitoring: Performance middleware and comprehensive logging

📊 **Current Benefits**: 70-95% performance improvement on critical endpoints
📁 **Detailed Status**: See OPTIMIZATION_STATUS.md for comprehensive optimization tracking