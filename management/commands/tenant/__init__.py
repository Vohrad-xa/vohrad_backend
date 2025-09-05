"""Tenant command module."""

from .create import create_tenant
import typer

app = typer.Typer(help="Tenant management commands")
app.command(name="create_tenant")(create_tenant)
