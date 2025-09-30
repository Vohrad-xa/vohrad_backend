"""Seed global roles and permissions command."""

import asyncio
from commands import CLIStyler, MessageType
from database.seeds.global_roles import create_global_roles
import sys
import typer

styler = CLIStyler()


def seed_global_roles():
    """Seed global roles and permissions into the shared schema."""
    styler.print_clean_header("Global Roles Seeding")

    try:
        styler.print_clean_message("Starting global roles seeding...", MessageType.INFO)
        asyncio.run(create_global_roles())
        styler.print_clean_message("Global roles seeding completed successfully!", MessageType.SUCCESS)
    except ImportError as e:
        styler.print_clean_message(f"Error importing seeding module: {e}", MessageType.ERROR)
        sys.exit(1)
    except Exception as e:
        styler.print_clean_message(f"Error during seeding: {e}", MessageType.ERROR)
        sys.exit(1)


if __name__ == "__main__":
    typer.run(seed_global_roles)
