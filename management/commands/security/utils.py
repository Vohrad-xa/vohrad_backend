"""Shared utilities for security commands."""
import os
from rich.console import Console

console = Console()


def get_environment() -> str:
    """Get current environment."""
    return os.getenv("ENVIRONMENT", "development")


def write_key_to_file(key_name: str, key_value: str, file_path: str) -> None:
    """Write key to file, replacing existing key if present."""
    key_line = f"{key_name}={key_value}\n"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # Remove existing key lines
        lines = [line for line in lines if not line.startswith(f"{key_name}=")]
        # Add new key
        lines.append(key_line)
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    except FileNotFoundError:
        # File doesn't exist, create it
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(key_line)

    os.chmod(file_path, 0o600)


def handle_key_output(key_name: str, key_value: str, to_file: str | None = None, show: bool = False) -> None:
    """Handle key output with production-safe patterns."""
    env = get_environment()

    if to_file:
        write_key_to_file(key_name, key_value, to_file)
        console.print(f"[bold green][SUCCESS] {key_name} written to {to_file}[/bold green]")
        console.print("[yellow][WARNING] File permissions set to 600 (owner-only)[/yellow]")
    elif show and env == "development":
        console.print(f"[bold green]Generated new {key_name}:[/bold green]")
        console.print(f"[dim]{key_name}=[/dim][bold]{key_value}[/bold]")
        console.print()
        console.print("[yellow][WARNING] Store this key securely and update your .env file[/yellow]")
        console.print("[red]Warning: Clear terminal history after viewing[/red]")
    elif env == "production":
        secure_file = ".env.new"
        write_key_to_file(key_name, key_value, secure_file)
        console.print(f"[bold green][SUCCESS] {key_name} generated securely[/bold green]")
        console.print(f"[yellow]Key written to {secure_file} (production-safe mode)[/yellow]")
        console.print("[dim]Use --to-file to specify custom location[/dim]")
    else:
        console.print(f"[bold green]{key_name} generated[/bold green]")
        console.print("[yellow]Use --show flag to display or --to-file to save securely[/yellow]")
