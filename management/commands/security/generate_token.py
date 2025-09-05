"""Generate JWT tokens for testing purposes."""

import asyncio
from commands import CLIStyler, MessageType
from database.sessions import with_default_db, with_tenant_db
from rich.prompt import IntPrompt
from security.jwt import JWTEngine, create_admin_access_payload, create_user_access_payload
import typer
from typing import Optional

styler = CLIStyler()
app = typer.Typer(help="Generate JWT tokens for testing")


class TokenGenerator:
    """Handles token generation for users and admins."""

    def __init__(self):
        self.jwt_engine = JWTEngine()

    async def list_admins(self) -> list[dict]:
        """List all active admins from shared schema."""
        from api.admin.models import Admin
        from sqlalchemy import select

        async with with_default_db() as db:
            result = await db.execute(
                select(Admin).where(Admin.is_active)
                .order_by(Admin.email)
            )
            admins = result.scalars().all()

            return [
                {
                    "id": admin.id,
                    "email": admin.email,
                    "role": admin.role,
                    "name": f"{admin.first_name or ''} {admin.last_name or ''}".strip() or "N/A",
                    "type": "admin"
                }
                for admin in admins
            ]

    async def list_users_by_tenant(self) -> dict[str, list[dict]]:
        """List all users grouped by tenant."""
        from api.tenant.models import Tenant
        from api.user.models import User
        from sqlalchemy import select

        # Get all tenants
        async with with_default_db() as db:
            result = await db.execute(
                select(Tenant).where(Tenant.status == "active")
                .order_by(Tenant.sub_domain)
            )
            tenants = result.scalars().all()

        users_by_tenant = {}

        for tenant in tenants:
            async with with_tenant_db(tenant.tenant_schema_name) as tenant_db:
                result = await tenant_db.execute(
                    select(User).order_by(User.email)
                )
                users = result.scalars().all()

                users_by_tenant[tenant.sub_domain] = [
                    {
                        "id": user.id,
                        "email": user.email,
                        "role": user.role or "user",
                        "name": f"{user.first_name or ''} {user.last_name or ''}".strip() or "N/A",
                        "tenant_id": user.tenant_id,
                        "tenant_name": tenant.sub_domain,
                        "type": "user"
                    }
                    for user in users
                ]

        return users_by_tenant

    def display_selection_table(self, admins: list[dict], users_by_tenant: dict[str, list[dict]]) -> list[dict]:
        """Display a numbered table of all users and admins for selection."""
        from rich.table import Table

        all_items = []
        table = Table(show_header=True, header_style="bold blue", border_style="dim blue")
        table.add_column("#", style="dim cyan", width=4)
        table.add_column("Type", style="magenta", width=8)
        table.add_column("Email", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Role", style="yellow")
        table.add_column("Tenant", style="green")

        index = 1

        # Add admins
        for admin in admins:
            table.add_row(
                str(index),
                "Admin",
                admin["email"],
                admin["name"],
                admin["role"],
                "Global"
            )
            all_items.append(admin)
            index += 1

        # Add users by tenant
        for tenant_name, users in users_by_tenant.items():
            if users:  # Only show tenants that have users
                for user in users:
                    table.add_row(
                        str(index),
                        "User",
                        user["email"],
                        user["name"],
                        user["role"],
                        tenant_name
                    )
                    all_items.append(user)
                    index += 1

        styler.console.print("\n[bold blue]Available Users and Admins for Token Generation[/bold blue]")
        styler.console.print(table)
        return all_items

    async def generate_token_for_selection(self, selected_item: dict, expires_in_days: Optional[int] = None) -> str:
        """Generate JWT token for the selected user or admin."""
        if selected_item["type"] == "admin":
            payload = create_admin_access_payload(
                admin_id=selected_item["id"],
                email=selected_item["email"]
            )
        else:
            payload = create_user_access_payload(
                user_id=selected_item["id"],
                email=selected_item["email"],
                tenant_id=selected_item["tenant_id"]
            )

        # Override expiration if custom days specified
        if expires_in_days is not None:
            from datetime import datetime, timedelta, timezone
            now = datetime.now(timezone.utc)
            custom_expires = now + timedelta(days=expires_in_days)
            payload["exp"] = int(custom_expires.timestamp())

        return self.jwt_engine.encode_token(payload)


@app.command("generate")
def generate_token(
    expires_in_days: Optional[int] = typer.Option(
        None,
        "--expires-in",
        "-e",
        help="Token expiration time in days (default: 1 day)"
    ),
    show_payload: bool = typer.Option(
        False,
        "--show-payload",
        "-p",
        help="Show the token payload for debugging"
    )
):
    """Generate JWT token by selecting from available users and admins."""

    async def _generate():
        generator = TokenGenerator()

        try:
            # Fetch all users and admins
            styler.print_clean_message("Loading users and admins...", MessageType.INFO)
            admins = await generator.list_admins()
            users_by_tenant = await generator.list_users_by_tenant()

            # Check if we have any users or admins
            total_users = sum(len(users) for users in users_by_tenant.values())
            if not admins and total_users == 0:
                styler.print_clean_message("No active users or admins found in the system.", MessageType.ERROR)
                return

            # Display selection table
            all_items = generator.display_selection_table(admins, users_by_tenant)

            if not all_items:
                styler.print_clean_message("No users or admins available for token generation.", MessageType.ERROR)
                return

            # Get user selection
            styler.console.print("\n")
            try:
                selection = IntPrompt.ask(
                    "Select a user/admin by number",
                    default=1,
                    show_default=True
                )

                if selection < 1 or selection > len(all_items):
                    styler.print_clean_message(
                        f"Invalid selection. Please choose between 1 and {len(all_items)}.",
                        MessageType.ERROR
                    )
                    return

                selected_item = all_items[selection - 1]

            except (ValueError, KeyboardInterrupt):
                styler.print_clean_message("Token generation cancelled.", MessageType.WARNING)
                return

            # Prompt for token duration if not provided via command line
            final_expires_in_days = expires_in_days
            if expires_in_days is None:
                styler.console.print("\n")
                try:
                    final_expires_in_days = IntPrompt.ask(
                        "Token validity duration in days",
                        default=1,
                        show_default=True
                    )

                    if final_expires_in_days <= 0:
                        styler.print_clean_message("Duration must be greater than 0 days.", MessageType.ERROR)
                        return

                except (ValueError, KeyboardInterrupt):
                    styler.print_clean_message("Token generation cancelled.", MessageType.WARNING)
                    return

            # Generate token
            styler.print_clean_message(
                f"Generating token for {selected_item['email']} ({selected_item['type']})...",
                MessageType.INFO
            )
            token = await generator.generate_token_for_selection(selected_item, final_expires_in_days)

            # Display results
            styler.console.print("\n")
            styler.print_clean_message("JWT Token generated successfully!", MessageType.SUCCESS)

            # Show token details using CLI utility
            details_data = {
                "User Type": selected_item["type"].title(),
                "Email": selected_item["email"],
                "Role": selected_item["role"],
                "Expires In": f"{final_expires_in_days} days"
            }

            if selected_item["type"] == "user":
                details_data["Tenant"] = selected_item["tenant_name"]

            styler.print_clean_table(details_data, "Token Details")

            # Show token
            styler.console.print("\n")
            styler.console.print("[bold cyan]JWT Token:[/bold cyan]")
            styler.console.print(f"[green]{token}[/green]")

            if show_payload:
                try:
                    decoded = generator.jwt_engine.decode_token(token)
                    styler.console.print("\n[bold cyan]Token Payload:[/bold cyan]")
                    styler.console.print(decoded)
                except Exception as e:
                    styler.print_clean_message(f"Could not decode token for display: {e}", MessageType.WARNING)

            styler.console.print("\n")
            styler.print_clean_message("You can now use this token for API testing and development.", MessageType.INFO)
            styler.print_clean_message("Remember: This token is for testing purposes only!", MessageType.WARNING)

        except Exception as e:
            styler.print_clean_message(f"Failed to generate token: {e}", MessageType.ERROR)
            raise

    asyncio.run(_generate())


if __name__ == "__main__":
    app()
