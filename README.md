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
src/
├── api/           # API endpoints and routing
├── config/        # Application configuration
├── database/      # Data layer and models
├── services/      # Business logic layer
└── main.py        # Application entry point

migrations/        # Database schema versions
management/        # CLI administration tools
```

## License

MIT