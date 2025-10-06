"""User creation command with role assignment."""

from api.admin.models import Admin
from api.assignment.models import Assignment
from api.common.validators import CommonValidators
from api.role.models import Role
from api.tenant.models import Tenant
from api.tenant.service import TenantService
from api.user.models import User
import asyncio
import bcrypt
from commands import CLIStyler
from constants.enums import RoleScope
from database.sessions import with_default_db, with_tenant_db
import inquirer
import logging
from sqlalchemy import select
import typer
from typing import Optional
from uuid import UUID, uuid4

logging.disable(logging.INFO)

styler = CLIStyler()


def validate_password_input() -> str:
    """Validate password input with professional feedback."""
    while True:
        password = typer.prompt("Password *", hide_input=True)
        try:
            CommonValidators.validate_password_strength(password)
            return password
        except ValueError as e:
            styler.print_clean_message(f"Password validation failed: {e!s}", "ERROR")
            styler.console.print("Requirements:")
            styler.console.print("  Minimum 8 characters")
            styler.console.print("  At least one uppercase letter")
            styler.console.print("  At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)")
            styler.print_clean_message("Please try again.", "INFO")


async def _get_available_tenants():
    """Fetch and return available active tenants."""
    async with with_default_db() as db:
        result = await db.execute(select(Tenant).where(Tenant.status == "active").order_by(Tenant.sub_domain))
        return result.scalars().all()


async def _create_user_with_role_async():
    """Create a new user (system admin or regular user) and assign role in one command."""
    styler.console.clear()

    # Use clean header styling
    styler.print_clean_header("User Creation with Role Assignment")

    styler.print_clean_message("Choose the type of user you want to create:", "INFO")
    styler.console.print("  1. Administrator - Full system access")
    styler.console.print("  2. Tenant User - Access within specific tenant")

    user_type_choices = [
        inquirer.List(
            "user_type",
            message="Select user type",
            choices=[("System Administrator (Global Access)", "1"), ("Tenant User (Organization Access)", "2")],
            default="2",
        )
    ]
    answers = inquirer.prompt(user_type_choices)
    user_type = answers["user_type"]
    is_admin = user_type == "1"

    styler.print_clean_message("Please provide the following user details:", "INFO")
    styler.console.print("  All fields marked with * are required")
    styler.console.print("  Password will be hidden during input")

    email = typer.prompt("Email address *", type=str)
    password = validate_password_input()
    first_name = typer.prompt("First name *", type=str)
    last_name = typer.prompt("Last name *", type=str)
    phone = typer.prompt("Phone number (optional)", default="", show_default=False)

    if is_admin:
        styler.print_clean_message("Creating administrator...", "STEP")
        await _create_admin_with_role(email, password, first_name, last_name, phone)
    else:
        styler.print_clean_message("Selecting tenant...", "STEP")
        available_tenants = await _get_available_tenants()
        if not available_tenants:
            styler.print_clean_message(
                "No active tenants found. Please create a tenant first using the tenant management commands.", "ERROR"
            )
            return

        tenant_choices = []
        for tenant in available_tenants:
            display_parts = [tenant.sub_domain]
            if tenant.email:
                display_parts.append(f"({tenant.email})")
            if tenant.city:
                display_parts.append(f"- {tenant.city}")

            display_text = " ".join(display_parts)
            tenant_choices.append((display_text, tenant))

        tenant_question = [inquirer.List("tenant", message="Select target tenant", choices=tenant_choices)]

        tenant_answers = inquirer.prompt(tenant_question)
        selected_tenant = tenant_answers["tenant"]
        styler.print_clean_message("Creating user...", "STEP")
        await _create_user_with_role(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            tenant_id=selected_tenant.tenant_id,
            phone=phone if phone else None,
        )


def create_user_with_role():
    """Synchronous wrapper for the async create_user_with_role function."""
    asyncio.run(_create_user_with_role_async())


async def _create_admin_with_role(email: str, password: str, first_name: str, last_name: str, phone: Optional[str] = None):
    """Create admin user and assign global role."""
    async with with_default_db() as db:
        try:
            # Check if admin already exists
            existing = await db.execute(select(Admin).where(Admin.email == email))
            if existing.scalar_one_or_none():
                styler.print_clean_message(
                    f"An administrator with email '{email}' already exists. Please use a different email address.", "ERROR"
                )
                return

            # Show available global roles (restricted to system roles)
            roles_result = await db.execute(select(Role).where(Role.role_scope == RoleScope.GLOBAL, Role.is_active))
            # Only allow core system global roles
            global_roles_all = roles_result.scalars().all()
            global_roles = [r for r in global_roles_all if r.name in ("super_admin", "admin")]

            if not global_roles:
                styler.print_clean_message(
                    "No global roles found. Please create global roles first using the role management commands.", "ERROR"
                )
                return

            role_choices = []
            for role in global_roles:
                desc = role.description if role.description else "No description available"
                display_text = f"{role.name} - {desc}"
                role_choices.append((display_text, role))

            role_question = [inquirer.List("role", message="Choose role for this administrator", choices=role_choices)]

            role_answers = inquirer.prompt(role_question)
            selected_role = role_answers["role"]

            selected_role_name = selected_role.name
            selected_role_id = selected_role.id

            hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            admin_id = uuid4()
            admin = Admin(
                id=admin_id,
                email=email,
                password=hashed_password,
                first_name=first_name,
                last_name=last_name,
                role=selected_role_name,
                phone_number=phone,
                is_active=True,
            )

            db.add(admin)
            await db.flush()

            assignment = Assignment(user_id=admin_id, role_id=selected_role_id, assigned_by=admin_id)

            db.add(assignment)
            await db.commit()

            # Use clean success messaging
            styler.print_clean_message("Administrator created successfully!", "SUCCESS")

            # Use clean table styling
            table_data = {
                "Email Address": email,
                "Full Name": f"{first_name} {last_name}",
                "Role": selected_role_name,
                "User ID": str(admin_id),
                "Status": "Active",
            }
            styler.print_clean_table(table_data, "Administrator Details")

        except Exception as e:
            await db.rollback()
            styler.print_clean_message(f"Failed to create administrator: {e!s}", "ERROR")
            raise


async def _create_user_with_role(
    email: str, password: str, first_name: str, last_name: str, tenant_id: UUID, phone: Optional[str] = None
):
    """Create regular user and assign tenant role."""
    try:
        async with with_default_db() as shared_db:
            tenant_service = TenantService()
            tenant = await tenant_service.get_tenant_by_id(shared_db, tenant_id)
            if not tenant:
                styler.print_clean_message(f"Tenant '{tenant_id}' not found", "ERROR")
                return

            tenant_schema = tenant.tenant_schema_name
            tenant_subdomain = tenant.sub_domain

        async with with_tenant_db(tenant_schema) as tenant_db:
            existing = await tenant_db.execute(select(User).where(User.email == email))
            if existing.scalar_one_or_none():
                styler.print_clean_message(
                    f"A user with email '{email}' already exists in '{tenant_subdomain}'. Use a different email address.", "ERROR"
                )
                return

            roles_result = await tenant_db.execute(select(Role).where(Role.role_scope == RoleScope.TENANT, Role.is_active))
            tenant_roles_all = roles_result.scalars().all()

            # Safety: forbid global admin role names in tenant context
            forbidden_in_tenant = {"admin", "super_admin"}
            tenant_roles = [r for r in tenant_roles_all if r.name not in forbidden_in_tenant]

            if not tenant_roles:
                styler.print_clean_message(
                    f"No tenant roles found for '{tenant_subdomain}'. Please create tenant roles first.", "ERROR"
                )
                return

            role_choices = []
            for role in tenant_roles:
                desc = role.description if role.description else "No description available"
                display_text = f"{role.name} - {desc}"
                role_choices.append((display_text, role))

            role_question = [inquirer.List("role", message=f"Select role for user in '{tenant_subdomain}'", choices=role_choices)]

            role_answers = inquirer.prompt(role_question)
            selected_role = role_answers["role"]

            selected_role_id = selected_role.id
            selected_role_name = selected_role.name

            hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            user_id = uuid4()
            user = User(
                id=user_id,
                tenant_id=tenant_id,  # Associate user with tenant
                email=email,
                password=hashed_password,
                first_name=first_name,
                last_name=last_name,
                role=selected_role_name,
                phone_number=phone,
            )

            tenant_db.add(user)
            await tenant_db.flush()

            assignment = Assignment(user_id=user_id, role_id=selected_role_id, assigned_by=user_id)

            tenant_db.add(assignment)
            await tenant_db.commit()

            # Use clean success messaging
            styler.print_clean_message("User created successfully!", "SUCCESS")

            # Use clean table styling
            table_data = {
                "Email Address": email,
                "Full Name": f"{first_name} {last_name}",
                "Tenant": tenant_subdomain,
                "Tenant ID": str(tenant_id),
                "Role": selected_role_name,
                "User ID": str(user_id),
                "Status": "Active",
            }
            styler.print_clean_table(table_data, "User Details")

    except Exception as e:
        styler.print_clean_message(f"Failed to create user: {e!s}", "ERROR")
        raise


if __name__ == "__main__":
    asyncio.run(_create_user_with_role_async())
