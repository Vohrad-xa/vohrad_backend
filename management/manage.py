"""Management command entry point."""

from commands import security, tenant, user
import typer

app = typer.Typer(help="Vohrad management commands")
app.add_typer(security.app, name="security", help="Security and key management commands")
app.add_typer(tenant.app, name="tenant", help="Tenant management commands")
app.add_typer(user.app, name="user", help="User management commands")


@app.command()
def info():
    """Show application information."""
    typer.echo("Vohrad Multi-tenant API")
    typer.echo("Version: 1.0.0")
    typer.echo("Management commands ready")


if __name__ == "__main__":
    app()
