"""Seed tenant roles and permissions command."""

import asyncio
from commands import CLIStyler, MessageType
from database.seeds.tenant_roles import create_tenant_roles
import sys
import typer

styler = CLIStyler()


def seed_tenant_roles():
    """Seed tenant roles and permissions into all tenant schemas."""
    styler.print_clean_header("Tenant Roles Seeding")

    try:
        styler.print_clean_message("Starting tenant roles seeding...", MessageType.INFO)
        asyncio.run(create_tenant_roles())
        styler.print_clean_message("Tenant roles seeding completed successfully!", MessageType.SUCCESS)
    except ImportError as e:
        styler.print_clean_message(f"Error importing seeding module: {e}", MessageType.ERROR)
        sys.exit(1)
    except Exception as e:
        styler.print_clean_message(f"Error during seeding: {e}", MessageType.ERROR)
        sys.exit(1)


if __name__ == "__main__":
    typer.run(seed_tenant_roles)
