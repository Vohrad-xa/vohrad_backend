"""User management commands."""

import asyncio
import sys
import typer
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent / "src"))
from api.tenant.service import TenantService
from api.user.models import User
from api.user.schema import UserCreate
from api.user.service import UserService
from database.sessions import with_default_db
from database.sessions import with_tenant_db
from typing import Optional
from uuid import UUID

app = typer.Typer()


@app.command()
def create_user():
    """Create a new user for a specific tenant."""
    email       = typer.prompt("User email address")
    password    = typer.prompt("User password", hide_input=True)
    first_name  = typer.prompt("User first name")
    last_name   = typer.prompt("User last name")
    tenant_id   = typer.prompt("Tenant ID (UUID)")
    tenant_role = typer.prompt("User role in tenant (owner, admin, user, viewer)", default="user")
    phone       = typer.prompt("User phone number", default=None)
    asyncio.run(
        _create_user(
            email       = email,
            password    = password,
            first_name  = first_name,
            last_name   = last_name,
            tenant_id   = UUID(tenant_id),
            tenant_role = tenant_role,
            phone       = phone,
        )
    )


async def _create_user(
  email      : str,
  password   : str,
  first_name : str,
  last_name  : str,
  tenant_id  : UUID,
  tenant_role: str,
  phone      : Optional[str] = None,
) -> User    :
    """Create a new user for a specific tenant."""
    try:
        user_service   = UserService()
        tenant_service = TenantService()

        async with with_default_db() as db:
            tenant = await tenant_service.get_by_id(db, tenant_id)
            if not tenant:
                typer.echo(f"Tenant with ID {tenant_id} not found", err=True)
                raise typer.Exit(1)

            typer.echo(f"📋 Found tenant: {tenant.sub_domain} (schema: {tenant.tenant_schema_name})")

        user_data = UserCreate(
            email       = email,
            password    = password,
            first_name  = first_name,
            last_name   = last_name,
            tenant_role = tenant_role,
            phone       = phone,
        )

        async with with_tenant_db(tenant.tenant_schema_name) as tenant_db:
            user = await user_service.create_user(tenant_db, user_data, tenant)

            typer.echo(" User created successfully!")
            typer.echo(f" ID: {user.id}")
            typer.echo(f" Email: {user.email}")
            typer.echo(f" Name: {user.first_name} {user.last_name}")
            typer.echo(f" Role: {user.tenant_role}")
            typer.echo(f" Tenant: {tenant.sub_domain} ({tenant.tenant_schema_name})")

            return user

    except Exception as e:
        typer.echo(f"Error creating user: {e!s}", err=True)
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
