"""Tenant command module."""

import typer
from .create import create_tenant

app = typer.Typer(help="Tenant management commands")
app.command(name="create_tenant")(create_tenant)
