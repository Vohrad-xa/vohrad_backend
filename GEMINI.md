# Vohrad Project Analysis

## Project Overview

Vohrad is an enterprise-grade, multi-tenant inventory management platform designed for scalability and performance. It is a Software-as-a-Service (SaaS) solution that uses a schema-isolated, multi-tenant data architecture to ensure complete tenant data isolation while maintaining operational efficiency.

The application is built with a modern Python technology stack, including:

*   **FastAPI**: A high-performance web framework for building APIs.
*   **SQLAlchemy**: An asyncio-compatible Object-Relational Mapper (ORM) for database interactions.
*   **PostgreSQL**: A powerful, open-source object-relational database system.
*   **Alembic**: A lightweight database migration tool for SQLAlchemy.
*   **PDM**: A modern Python package manager.
*   **Ruff**: An extremely fast Python linter and code formatter.
*   **MyPy**: A static type checker for Python.
*   **Pytest**: A mature, full-featured Python testing tool.

## Building and Running

### Prerequisites

*   Python 3.13
*   PDM (Python Dependency Management)

### Setup and Installation

1.  **Install dependencies**:
    ```bash
    pdm install --no-self
    ```

2.  **Configure environment**:
    Copy the example environment file and customize it with your settings.
    ```bash
    cp .env.example .env
    ```

3.  **Initialize the database**:
    This command applies all pending database migrations.
    ```bash
    alembic upgrade head
    ```

### Running the Application

*   **Start the development server**:
    ```bash
    pdm run start
    ```
    The API will be available at `http://127.0.0.1:8000`.

*   **API Documentation**:
    Interactive API documentation (Swagger UI) is available at `/docs` when the development server is running.

### Running Tests

*   **Execute the test suite**:
    ```bash
    pytest
    ```

## Development Conventions

### Code Style and Linting

*   The project uses **Ruff** for linting and code formatting. The configuration is defined in the `ruff.toml` file.
*   **Pre-commit hooks** are configured in `.pre-commit-config.yaml` to automatically check and format code before committing.

### Database Migrations

*   Database schema changes are managed through **Alembic**. Migration scripts are located in the `migrations/versions` directory.

### Management Commands

*   The project includes a command-line interface (CLI) for management tasks, built with **Typer**. The main entry point for the CLI is `management/manage.py`.
*   You can run management commands using `pdm run manage <command>`. For example, to create a new tenant, you would run:
    ```bash
    pdm run manage tenant create <tenant_name>
    ```
