"""License management commands."""

from .create import create_license
from .send_expiry_reminders import send_expiry_reminders
import typer

app = typer.Typer(help="License management commands")
app.command("create")(create_license)
app.command("send-expiry-reminders")(send_expiry_reminders)

__all__ = ["app", "create_license", "send_expiry_reminders"]
