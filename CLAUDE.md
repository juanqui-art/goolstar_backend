# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- **Run server**: `python manage.py runserver`
- **Run tests**: `python manage.py test`
- **Run single test**: `python manage.py test api.tests.TestClassName.test_method_name`
- **Create migrations**: `python manage.py makemigrations`
- **Apply migrations**: `python manage.py migrate`
- **Lint code**: `flake8`
- **Check types**: `mypy .`

## Code Style Guidelines

- **Imports**: Group imports in this order: standard library, Django/DRF, third-party packages, local apps
- **Formatting**: Follow PEP 8 conventions with 4-space indentation
- **Models**: Define `__str__` methods and Meta classes as needed; add docstrings for model classes
- **Validation**: Use Django's clean/validation methods and model validators
- **Error Handling**: Use Django exceptions (ValidationError, PermissionDenied) appropriately
- **Naming**: Use lowercase with underscores for variables/functions; CamelCase for classes
- **Documentation**: Add docstrings to models, views, and complex functions
- **Security**: Never hardcode secrets; use environment variables loaded via python-dotenv