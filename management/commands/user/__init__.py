"""User command module."""
import typer
from .create import create_user

# Main user app
app = typer.Typer(help="User management commands")

# Register commands
app.command()(create_user)
