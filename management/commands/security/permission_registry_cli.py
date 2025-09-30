"""Permission registry management CLI."""

from commands import CLIEnvironment
from commands.cli_utils import CLIStyler, MessageType
from rich.table import Table
from security.policy import PermissionSupportLevel, get_support_level, is_allowed_for_custom_role
import typer

app = typer.Typer(help="Manage permission support-level registry")
styler = CLIStyler()


@app.command("list")
def list_permissions() -> None:
    """List permission registry entries and levels."""
    from security.policy.permission_registry import PERMISSION_SUPPORT_REGISTRY

    if not PERMISSION_SUPPORT_REGISTRY:
        styler.print_warning("No registry entries found")
        return

    table = Table(show_header=True, header_style="bold blue", border_style="dim blue")
    table.add_column("Resource", style="cyan")
    table.add_column("Action", style="cyan")
    table.add_column("Level", style="yellow")

    for (resource, action), level in sorted(PERMISSION_SUPPORT_REGISTRY.items()):
        table.add_row(resource, action, level.value)

    env = CLIEnvironment.get_environment()
    styler.print_clean_message(f"Environment: {env}", MessageType.INFO)
    styler.console.print(table)


@app.command("check")
def check_permission(
    resource: str = typer.Argument(..., help="Permission resource (e.g., user)"),
    action: str = typer.Argument(..., help="Permission action (e.g., read)"),
) -> None:
    """Check a permission's level and whether a custom role may use it now."""
    level = get_support_level(resource, action)
    allowed, reason = is_allowed_for_custom_role(resource, action)

    data = {
        "resource.action"        : f"{resource}.{action}",
        "level"                  : (level.value if level else "UNKNOWN"),
        "allowed_for_custom_role": "yes" if allowed else "no",
    }
    if reason and not allowed:
        data["reason"] = reason

    styler.print_clean_table(data, title="Permission Registry Check")


@app.command("snippet")
def generate_snippet(
    resource: str = typer.Argument(..., help="Permission resource (e.g., user)"),
    action  : str = typer.Argument(..., help="Permission action (e.g., read)"),
    level   : PermissionSupportLevel = typer.Argument(..., help="Level: SUPPORTED|TESTING|NOT_SUPPORTED"),
) -> None:
    """Generate a code snippet to add/update the registry entry."""
    key = (resource.strip().lower(), action.strip().lower())
    snippet = f"    {key!r}: PermissionSupportLevel.{level.name},"
    styler.print_clean_message("Add the following line to PERMISSION_SUPPORT_REGISTRY:", MessageType.INFO)
    styler.console.print(f"[green]{snippet}[/green]")
