"""User command module."""

from .create_with_role import create_user_with_role
import typer

# Main user app
app = typer.Typer(help="User management commands")

# Register commands
app.command(name="create-with-role")(create_user_with_role)
