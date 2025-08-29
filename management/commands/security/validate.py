"""Security key validation commands."""
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root / "src"))
os.chdir(project_root)

from config.keys import get_key_manager  # noqa: E402

console = Console()


def validate_keys():
    """Validate application security keys and configuration."""
    console.print("[bold blue]Security Key Validation Report[/bold blue]")
    console.print()

    key_manager = get_key_manager()
    status = key_manager.validate_keys()

    # Create summary table
    table = Table(title="Key Configuration Status", show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")

    # Add table rows
    secret_configured = "[OK] Configured" if status["secret_key_configured"] else "[X] Missing"
    secret_strength = f"({status['secret_key_strength']} - {status['secret_key_length']} chars)"
    table.add_row("SECRET_KEY", secret_configured, secret_strength)

    enc_configured = "[OK] Configured" if status["encryption_key_configured"] else "[X] Missing"
    table.add_row("ENCRYPTION_KEY", enc_configured, "")

    table.add_row("JWT Algorithm", status["jwt_algorithm"], "")

    env_style = "production" if status["environment"] == "production" else "development"
    table.add_row("Environment", status["environment"], f"({env_style} mode)")

    console.print(table)
    console.print()

    # Show warnings
    if status["warnings"]:
        console.print("[bold red]Security Warnings:[/bold red]")
        for warning in status["warnings"]:
            console.print(f"   {warning}", style="yellow")
        console.print()
    else:
        console.print("[bold green][OK] No security warnings detected[/bold green]")
        console.print()

    # Security recommendations
    console.print("[bold blue]Security Recommendations:[/bold blue]")
    if status["environment"] == "production":
        if not status["secret_key_configured"]:
            console.print("  • Configure a strong SECRET_KEY for production", style="red")
        elif status["secret_key_strength"] == "weak":
            console.print("  • Use a stronger SECRET_KEY (64+ characters with special chars)", style="yellow")

        if not status["encryption_key_configured"]:
            console.print("  • Consider setting a dedicated ENCRYPTION_KEY", style="yellow")

        console.print("  • Regularly rotate security keys", style="dim")
        console.print("  • Use environment-specific key management", style="dim")
