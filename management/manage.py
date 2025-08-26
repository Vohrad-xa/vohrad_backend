"""Management command entry point."""

import typer
from commands import tenant

app = typer.Typer(help="Vohrad management commands")
app.add_typer(tenant.app, name="tenant", help="Tenant management commands")

@app.command()
def info():
    """Show application information."""
    typer.echo("Vohrad Multi-tenant API")
    typer.echo("Version: 1.0.0")
    typer.echo("Management commands ready")

if __name__ == "__main__":
    app()
