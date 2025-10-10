"""Menu commands."""

from .main_menu import main_menu
import typer

app = typer.Typer(help="Interactive menu commands")
app.command("main")(main_menu)

__all__ = ["app", "main_menu"]
