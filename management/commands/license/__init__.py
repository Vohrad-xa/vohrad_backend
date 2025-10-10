"""License management commands."""

from .create import create_license
import typer

app = typer.Typer(help="License management commands")
app.command("create")(create_license)

__all__ = ["app", "create_license"]
