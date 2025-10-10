"""Main interactive menu for all management commands."""

from commands import CLIStyler, MessageType
import inquirer
import subprocess
import sys


def main_menu():
    """Show main menu of all available management commands organized by category."""
    styler = CLIStyler()
    styler.print_clean_header("Vohrad Management Menu")

    menu_options = [
        ("CREATE   > License                 - Create a new license for a tenant", "create-license"),
        ("CREATE   > Tenant                  - Create a new tenant", "create-tenant"),
        ("CREATE   > User                    - Create a new user with role", "create-user"),
        ("CREATE   > Token                   - Create a security token", "create-token"),
        ("SECURITY > Validate Keys           - Check security key configuration", "validate-keys"),
        ("SECURITY > Generate Secret         - Create new application secret", "generate-secret"),
        ("SECURITY > Generate Encryption Key - Create encryption key", "generate-encryption-key"),
        ("SECURITY > Generate JWT Keys       - Create JWT key pair", "generate-jwt-keys"),
        ("SECURITY > Seed Global Roles       - Initialize global RBAC roles", "seed-global-roles"),
        ("SECURITY > Seed Tenant Roles       - Initialize tenant RBAC roles", "seed-tenant-roles"),
        ("SECURITY > Permission Registry     - Manage permission registry", "perm-registry"),
        ("TOKEN    > Revoke All Tokens       - Invalidate all tokens", "revoke-all-tokens"),
        ("TOKEN    > Revoke Tenant Tokens    - Invalidate tenant tokens", "revoke-tenant-tokens"),
        ("TOKEN    > List Tenants            - Show all tenants", "list-tenants"),
        ("LICENSE  > Send Expiry Reminders   - Email license expiry notifications", "send-expiry-reminders"),
        ("APP      > Security Scan           - Run Bandit security analysis", "security-scan"),
        ("APP      > Audit Dependencies      - Check for vulnerable packages", "audit-dependencies"),
    ]

    questions = [
        inquirer.List(
            "command",
            message="Select a command to run",
            choices=menu_options,
        )
    ]

    answer = inquirer.prompt(questions)

    if answer is None:
        styler.print_clean_message("Operation cancelled", MessageType.WARNING)
        return

    selected_command = answer["command"]
    styler.print_clean_message(f"Running: pdm run {selected_command}", MessageType.INFO)
    styler.console.print()

    try:
        result = subprocess.run(
            ["pdm", "run", selected_command],
            check=False,
        )
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        styler.print_clean_message("Operation cancelled", MessageType.WARNING)
        sys.exit(1)
