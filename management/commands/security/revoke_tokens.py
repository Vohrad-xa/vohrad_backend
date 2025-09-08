"""Revoke JWT tokens command."""

import asyncio
from commands import CLIStyler, MessageType
from datetime import datetime, timezone
from rich.prompt import Confirm
from rich.table import Table
import sys
import typer
from uuid import UUID

styler = CLIStyler()
app = typer.Typer(help="Revoke JWT tokens")


class TokenRevocationService:
    """Service for revoking JWT tokens."""

    def __init__(self):
        pass

    async def get_tenant_users(self, tenant_id: UUID) -> list[dict]:
        """Get all users for a specific tenant."""
        from api.tenant.models import Tenant
        from api.user.models import User
        from database.sessions import with_default_db, with_tenant_db
        from sqlalchemy import select

        async with with_default_db() as db:
            result = await db.execute(select(Tenant).where(Tenant.tenant_id == tenant_id))
            tenant = result.scalar_one_or_none()

            if not tenant:
                return []

        async with with_tenant_db(tenant.tenant_schema_name) as tenant_db:
            result = await tenant_db.execute(select(User).order_by(User.email))
            users = result.scalars().all()

            return [
                {
                    "id": user.id,
                    "email": user.email,
                    "name": f"{user.first_name or ''} {user.last_name or ''}".strip() or "N/A",
                    "tenant_name": tenant.sub_domain,
                    "tenant_id": tenant.tenant_id,
                }
                for user in users
            ]

    async def get_all_tenants(self) -> list[dict]:
        """Get all active tenants."""
        from api.tenant.models import Tenant
        from database.sessions import with_default_db
        from sqlalchemy import select

        async with with_default_db() as db:
            result = await db.execute(select(Tenant).where(Tenant.status == "active").order_by(Tenant.sub_domain))
            tenants = result.scalars().all()

            return [
                {
                    "id": tenant.tenant_id,
                    "name": tenant.sub_domain,
                    "subdomain": tenant.sub_domain,
                    "schema": tenant.tenant_schema_name,
                }
                for tenant in tenants
            ]

    async def revoke_tenant_tokens(self, tenant_id: UUID) -> dict:
        """Revoke all tokens for users in a specific tenant using Claims-Based revocation."""
        from api.tenant.models import Tenant
        from api.user.models import User
        from database.sessions import with_default_db, with_tenant_db
        from sqlalchemy import select, update

        # Get tenant info
        async with with_default_db() as shared_db:
            result = await shared_db.execute(select(Tenant).where(Tenant.tenant_id == tenant_id))
            tenant = result.scalar_one_or_none()

            if not tenant:
                return {"tenant_found": False, "users_count": 0, "revoked_count": 0}

        # Update tokens_valid_after for all users in tenant
        async with with_tenant_db(tenant.tenant_schema_name) as tenant_db:
            now = datetime.now(timezone.utc)
            result = await tenant_db.execute(update(User).values(tokens_valid_after=now))
            affected_rows = result.rowcount
            await tenant_db.commit()

        return {
            "tenant_found": True,
            "users_count": affected_rows,
            "revoked_count": affected_rows,
            "tenant_name": tenant.sub_domain,
        }

    async def revoke_all_tokens(self) -> dict:
        """Revoke all tokens across all tenants and admins using Claims-Based revocation."""
        from api.admin.models import Admin
        from database.sessions import with_default_db
        from security.jwt.revocation import get_jwt_revocation_service
        from sqlalchemy import select

        revocation_service = get_jwt_revocation_service()
        total_revoked = 0
        user_count = 0
        admin_count = 0

        # Get all admin IDs and revoke their tokens
        async with with_default_db() as shared_db:
            admin_result = await shared_db.execute(select(Admin.id).where(Admin.is_active))
            admin_ids = admin_result.scalars().all()

        for admin_id in admin_ids:
            revoked = await revocation_service.revoke_user_tokens(admin_id, "system_wide_revocation")
            admin_count += revoked

        # Get all user IDs and revoke their tokens
        tenants = await self.get_all_tenants()
        for tenant in tenants:
            users = await self.get_tenant_users(tenant["id"])
            for user in users:
                revoked = await revocation_service.revoke_user_tokens(user["id"], "system_wide_revocation")
                user_count += revoked

        total_revoked = user_count + admin_count

        return {
            "revoked_count": total_revoked,
            "user_count": user_count,
            "admin_count": admin_count,
            "tenant_count": len(tenants),
        }

    async def _display_tenants_table(self):
        """Display tenants table - DRY helper method."""
        styler.print_clean_header("Active Tenants")
        tenants = await self.get_all_tenants()

        if not tenants:
            styler.print_clean_message("No active tenants found", MessageType.WARNING)
            return

        table = Table(show_header=True, header_style="bold blue", border_style="dim blue")
        table.add_column("Tenant ID", style="dim cyan")
        table.add_column("Name", style="white")
        table.add_column("Subdomain", style="yellow")
        table.add_column("Schema", style="green")

        for tenant in tenants:
            table.add_row(str(tenant["id"]), tenant["name"], tenant["subdomain"], tenant["schema"])

        styler.console.print(f"\n[bold blue]Found {len(tenants)} active tenants[/bold blue]")
        styler.console.print(table)
        styler.console.print("\n[dim]Use tenant ID for token revocation[/dim]")


@app.command("tenant")
def revoke_tenant_tokens(
    tenant_id: str = typer.Argument(None, help="Tenant ID to revoke tokens for (optional - will show selection if not provided)"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
):
    """Revoke all JWT tokens for users in a specific tenant."""

    async def _revoke_tenant():
        service = TokenRevocationService()

        # If no tenant_id provided, show interactive selection
        if not tenant_id:
            tenants = await service.get_all_tenants()

            if not tenants:
                styler.print_clean_message("No active tenants found", MessageType.WARNING)
                return

            # Create choices for inquirer (display name -> tenant object)
            import inquirer

            choices = [f"{tenant['name']} ({tenant['subdomain']}) - {tenant['id']}" for tenant in tenants]

            styler.print_clean_header("Select Tenant for Token Revocation")
            questions = [inquirer.List("tenant", message="Use arrow keys to select tenant", choices=choices, carousel=True)]

            answers = inquirer.prompt(questions)
            if not answers:
                styler.print_clean_message("Selection cancelled", MessageType.WARNING)
                return

            # Extract tenant ID from selected choice
            selected_choice = answers["tenant"]
            selected_tenant_id = selected_choice.split(" - ")[-1]
            tenant_uuid = UUID(selected_tenant_id)
        else:
            try:
                tenant_uuid = UUID(tenant_id)
            except ValueError:
                styler.print_clean_message(f"Invalid tenant ID format: {tenant_id}", MessageType.ERROR)
                return

        styler.print_clean_header("Tenant Token Revocation")

        try:
            styler.print_clean_message("Loading tenant information...", MessageType.INFO)
            users = await service.get_tenant_users(tenant_uuid)

            if not users:
                styler.print_clean_message("No tenant found or no users in tenant", MessageType.ERROR)
                sys.exit(1)

            tenant_name = users[0]["tenant_name"]

            tenant_details = {"Tenant ID": str(tenant_uuid), "Tenant Subdomain": tenant_name, "Users Found": str(len(users))}
            styler.print_clean_table(tenant_details, "Tenant Information")

            if not force:
                styler.console.print(
                    f"\n[bold red]Warning:[/bold red] This will revoke ALL active JWT tokens for "
                    f"{len(users)} users in tenant '{tenant_name}'"
                )

                if not Confirm.ask("Are you sure you want to proceed?", default=False):
                    styler.print_clean_message("Token revocation cancelled", MessageType.WARNING)
                    return

            styler.print_clean_message(f"Revoking tokens for {len(users)} users...", MessageType.INFO)
            result = await service.revoke_tenant_tokens(tenant_uuid)

            if result["tenant_found"]:
                styler.print_clean_message(
                    f"Successfully revoked {result['revoked_count']} tokens for "
                    f"{result['users_count']} users in tenant '{result['tenant_name']}'",
                    MessageType.SUCCESS,
                )
            else:
                styler.print_clean_message("Tenant not found", MessageType.ERROR)

        except Exception as e:
            styler.print_clean_message(f"Error revoking tenant tokens: {e}", MessageType.ERROR)
            raise

    asyncio.run(_revoke_tenant())


@app.command("all")
def revoke_all_tokens(force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt")):
    """Revoke ALL JWT tokens across the entire system (all tenants and admins)."""

    async def _revoke_all():
        styler.print_clean_header("System-Wide Token Revocation")
        service = TokenRevocationService()

        try:
            styler.print_clean_message("Gathering system information...", MessageType.INFO)
            tenants = await service.get_all_tenants()

            from api.admin.models import Admin
            from database.sessions import with_default_db
            from sqlalchemy import select

            async with with_default_db() as db:
                result = await db.execute(select(Admin).where(Admin.is_active))
                admins = result.scalars().all()

            # Count total users
            total_users = 0
            for tenant in tenants:
                users = await service.get_tenant_users(tenant["id"])
                total_users += len(users)

            system_overview = {
                "Total Tenants": str(len(tenants)),
                "Total Users": str(total_users),
                "Total Admins": str(len(admins)),
                "Total Accounts": str(total_users + len(admins)),
            }
            styler.print_clean_table(system_overview, "System Overview")

            if not force:
                styler.console.print("\n[bold red]DANGER:[/bold red] This will revoke ALL active JWT tokens system-wide!")
                styler.console.print(
                    f"[red]This affects {total_users + len(admins)} accounts across {len(tenants)} tenants[/red]"
                )
                styler.console.print("[red]All users and admins will need to log in again[/red]")

                if not Confirm.ask("\nAre you absolutely sure you want to proceed?", default=False):
                    styler.print_clean_message("System-wide token revocation cancelled", MessageType.WARNING)
                    return

                if not Confirm.ask("This action cannot be undone. Proceed with system-wide token revocation?", default=False):
                    styler.print_clean_message("System-wide token revocation cancelled", MessageType.WARNING)
                    return

            styler.print_clean_message("Starting system-wide token revocation...", MessageType.INFO)
            result = await service.revoke_all_tokens()

            revocation_summary = {
                "Tokens Revoked": str(result["revoked_count"]),
                "Users Affected": str(result["user_count"]),
                "Admins Affected": str(result["admin_count"]),
                "Tenants Processed": str(result["tenant_count"]),
            }
            styler.print_clean_table(revocation_summary, "Revocation Summary")

            styler.print_clean_message("System-wide token revocation completed successfully!", MessageType.SUCCESS)

        except Exception as e:
            styler.print_clean_message(f"Error during system-wide token revocation: {e}", MessageType.ERROR)
            raise

    asyncio.run(_revoke_all())


@app.command("list-tenants")
def list_tenants():
    """List all tenants for reference when revoking tokens."""

    async def _list_tenants():
        service = TokenRevocationService()

        try:
            await service._display_tenants_table()
        except Exception as e:
            styler.print_clean_message(f"Error listing tenants: {e}", MessageType.ERROR)
            raise

    asyncio.run(_list_tenants())


if __name__ == "__main__":
    app()
