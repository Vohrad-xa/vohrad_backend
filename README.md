# Vohrad

Enterprise-grade multi-tenant inventory management platform built for scalability and performance.

## Overview

Vohrad is a SaaS inventory management solution designed for businesses requiring isolated data environments. The platform leverages PostgreSQL schema-based multi-tenancy to ensure complete tenant isolation while maintaining operational efficiency.

## Architecture

- **Multi-tenant SaaS** - Schema-isolated tenant data with dynamic routing
- **RESTful API** - OpenAPI 3.0 compliant endpoints with comprehensive documentation
- **Async Operations** - High-performance asynchronous request handling
- **Type Safety** - Full static type checking and runtime validation
- **Database Migrations** - Version-controlled schema evolution

## Technology Stack

**Runtime**

- Python 3.13
- FastAPI
- PostgreSQL 14+
- SQLAlchemy 2.0 (async)
- Uvicorn ASGI server

**Development**

- PDM (package management)
- Alembic (migrations)
- Ruff (linting/formatting)
- MyPy (type checking)
- Pytest (testing)
- Pre-commit (code quality)

## Development Setup

```bash
# Install dependencies
pdm install --no-self

# Configure environment
cp .env.example .env

# Initialize database
alembic upgrade head

# Start development server
pdm run start
```

## API Documentation

Interactive API documentation available at `/docs` when running the development server.

## Project Structure

```
├── .env.example
├── alembic.ini
├── pyproject.toml                  # Project
├── pytest.ini
├── ruff.toml
├── management/                     # CLI
│   ├── commands/
│   │   ├── format.py
│   │   └── tenant.py
│   └── manage.py                   # Main management script
├── migrations/                     # Database schema versions
│   ├── env.py
│   ├── script.py.mako
│   ├── tenant.py                   # Tenant-default migration utilities
│   └── versions/
│       ├── 001_create_migration
│       └── 002_create_migration
└── src/                            # Application core
    ├── main.py                     # Application entry point
    ├── api/
    │   ├── common/
    │   │   ├── dependencies.py
    │   │   ├── router_utils.py
    │   │   ├── schemas.py
    │   │   └── validators.py
    │   ├── system/
    │   │   ├── models.py
    │   │   ├── service.py
    │   │   ├── schema.py
    │   │   └── router.py
    │   ├── tenant/
    │   │   ├── models.py
    │   │   ├── router.py
    │   │   ├── schema.py
    │   │   └── service.py
    │   └── user/
    │       ├── models.py
    │       ├── router.py
    │       ├── schema.py
    │       └── service.py
    ├── config/                     # Application configuration
    │   ├── logging-config.yml
    │   └── settings.py
    ├── constants/                  # Application constants
    │   ├── defaults.py
    │   ├── enums.py
    │   ├── messages.py
    │   └── validation.py
    ├── database/                   # Data layer and models
    │   ├── base.py
    │   ├── engine.py
    │   ├── sessions.py
    │   └── cache/
    │       ├── interface.py
    │       ├── lru_cache.py
    │       └── tenant_cache.py
    ├── domain/                     # Domain logic
    │   └── subdomain.py
    ├── exceptions/                 # Exception handling
    │   ├── application.py
    │   ├── base.py
    │   ├── domain.py
    │   ├── factory.py
    │   ├── infrastructure.py
    │   ├── integration.py
    │   └── registry.py
    ├── middleware/                 # HTTP middleware
    │   ├── auth.py
    │   ├── decorators.py
    │   ├── exception_handler.py
    │   └── logging_middleware.py
    ├── observability/              # Monitoring and logging
    │   ├── config.py
    │   ├── context.py
    │   ├── filters.py
    │   ├── formatters.py
    │   └── logger.py
    ├── security/                   # Security utilities
    │   └── key_manager.py
    ├── services/
    │   ├──
    │   └── base_service.py
    └── web/                        # Web utilities
        ├── pagination.py
        ├── response_factory.py
        └── responses.py
```

## License

MIT
