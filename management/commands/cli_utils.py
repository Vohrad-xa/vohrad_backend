"""Shared CLI utilities for consistent styling across management commands."""

from enum import Enum
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from typing import Dict, Optional

try:
    from config.settings import Settings
except ImportError:
    Settings = None


class MessageType(Enum):
    """Message types for consistent styling."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    STEP = "step"


class CLIStyler:
    """Centralized CLI styling utilities for consistent appearance across commands."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize CLI styler with optional console instance."""
        self.console = console or Console()

        self.colors = {
            MessageType.SUCCESS: {
                "border": "dim white",
                "title": "Success",
                "text": "white"
            },
            MessageType.ERROR: {
                "border": "dim white",
                "title": "Error",
                "text": "white"
            },
            MessageType.WARNING: {
                "border": "dim white",
                "title": "Warning",
                "text": "white"
            },
            MessageType.INFO: {
                "border": "dim white",
                "title": "Information",
                "text": "white"
            },
            MessageType.STEP: {
                "border": "dim white",
                "title": "Step",
                "text": "white"
            }
        }

    def print_clean_message(self, message: str, message_type: MessageType = MessageType.INFO) -> None:
        """Print a professional message with clean formatting."""
        type_colors = {
            MessageType.SUCCESS: "green",
            MessageType.ERROR: "red",
            MessageType.WARNING: "yellow",
            MessageType.INFO: "blue",
            MessageType.STEP: "cyan"
        }

        type_prefix = {
            MessageType.SUCCESS: "SUCCESS:",
            MessageType.ERROR: "ERROR:",
            MessageType.WARNING: "WARNING:",
            MessageType.INFO: "INFO:",
            MessageType.STEP: "STEP:"
        }

        color = type_colors.get(message_type, "white")
        prefix = type_prefix.get(message_type, "INFO:")
        self.console.print(f"[{color}]{prefix}[/{color}] {message}")

    def print_success(self, message: str) -> None:
        """Print a success message with green styling."""
        self.print_clean_message(message, MessageType.SUCCESS)

    def print_warning(self, message: str) -> None:
        """Print a warning message with yellow styling."""
        self.print_clean_message(message, MessageType.WARNING)

    def print_clean_header(self, title: str) -> None:
        """Print a professional header with clean styling."""
        self.console.clear()
        self.console.print(f"{title}", style="bold blue")

    def print_clean_table(self, data: Dict[str, str], title: Optional[str] = None) -> None:
        """Print a professional table with clean formatting."""
        if title:
            self.console.print(f"{title}", style="bold blue")

        if not data:
            return

        table = Table(show_header=True, header_style="bold blue", border_style="dim blue")
        table.add_column("Configuration", style="dim cyan", no_wrap=True)
        table.add_column("Value", style="white")

        for key, value in data.items():
            formatted_key = key.replace('_', ' ').title()
            table.add_row(formatted_key, value)

        self.console.print(table)


class CLIEnvironment:
    """Environment utilities for CLI commands."""

    @staticmethod
    def get_environment() -> str:
        """Get the current environment using Settings as single source of truth."""
        try:
            if Settings is not None:
                return Settings.instance().ENVIRONMENT
        except Exception:
            # Fallback to os.getenv if Settings fails
            pass
        return os.getenv("ENVIRONMENT", "development")

    @staticmethod
    def is_development() -> bool:
        """Check if running in development environment."""
        return CLIEnvironment.get_environment() == "development"

    @staticmethod
    def is_production() -> bool:
        """Check if running in production environment."""
        return CLIEnvironment.get_environment() == "production"

    @staticmethod
    def get_project_root() -> Path:
        """Get project root directory."""
        return Path(__file__).parent.parent.parent


class CLIFileUtils:
    """File utilities for CLI commands."""

    @staticmethod
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

    @staticmethod
    def handle_key_output(key_name: str, key_value: str, to_file: Optional[str] = None,
                         show: bool = False, styler: Optional[CLIStyler] = None) -> None:
        """Handle key output with production-safe patterns."""
        if styler is None:
            styler = CLIStyler()

        env = CLIEnvironment.get_environment()

        if to_file:
            CLIFileUtils.write_key_to_file(key_name, key_value, to_file)
            styler.print_success(f"{key_name} written to {to_file}")
            styler.print_warning("File permissions set to 600 (owner-only)")

        elif show and env == "development":
            styler.console.print(f"[bold green]Generated new {key_name}:[/bold green]")
            styler.console.print(f"[dim]{key_name}=[/dim][bold]{key_value}[/bold]")
            styler.console.print()
            styler.print_warning("Store this key securely and update your .env file")
            styler.console.print("[red]Warning: Clear terminal history after viewing[/red]")

        elif env == "production":
            env_file = ".env"
            CLIFileUtils.write_key_to_file(key_name, key_value, env_file)
            styler.print_success(f"{key_name} generated and updated in {env_file}")
            styler.console.print(f"[yellow]Key automatically updated in {env_file} (production-safe mode)[/yellow]")
            styler.console.print("[dim]Use --to-file to specify custom location[/dim]")

        else:
            env_file = ".env"
            CLIFileUtils.write_key_to_file(key_name, key_value, env_file)
            styler.print_success(f"{key_name} generated and updated in {env_file}")
            styler.console.print("[yellow]Use --show flag to display or --to-file to save to custom location[/yellow]")


# Note: Use CLIEnvironment.get_environment() and CLIFileUtils methods directly
