"""License creation command."""

from api.license.schema import LicenseCreate
from api.license.service import license_service
from api.stripe import stripe_payment_service
from api.tenant.models import Tenant
import asyncio
from commands import CLIStyler, MessageType
from database.sessions import with_default_db
from datetime import datetime
from decimal import Decimal
import inquirer
from sqlalchemy import select
import typer
from typing import Optional

styler = CLIStyler()


async def _get_available_tenants():
    """Fetch and return available active tenants."""
    async with with_default_db() as db:
        result = await db.execute(
            select(Tenant)
            .where(Tenant.status == "active")
            .order_by(Tenant.sub_domain)
        )
        return result.scalars().all()


async def _create_license_async():
    """Create a new license for a tenant."""
    styler.console.clear()

    # Use clean header styling
    styler.print_clean_header("License Creation")

    styler.print_clean_message("Select the tenant for this license:", MessageType.INFO)

    # Get available tenants
    available_tenants = await _get_available_tenants()
    if not available_tenants:
        styler.print_clean_message(
            "No active tenants found. Please create a tenant first using the tenant management commands.",
            MessageType.ERROR
        )
        return

    # Build tenant choices
    tenant_choices = []
    for tenant in available_tenants:
        display_parts = [tenant.sub_domain]
        if tenant.email:
            display_parts.append(f"({tenant.email})")
        if tenant.city:
            display_parts.append(f"- {tenant.city}")

        display_text = " ".join(display_parts)
        tenant_choices.append((display_text, tenant))

    tenant_question = [
        inquirer.List(
            "tenant",
            message="Select target tenant",
            choices=tenant_choices
        )
    ]

    tenant_answers = inquirer.prompt(tenant_question)
    selected_tenant = tenant_answers["tenant"]

    styler.print_clean_message("Please provide the following license details:", MessageType.INFO)
    styler.console.print("  All fields marked with * are required")
    styler.console.print("  Seats: Number of users allowed (must be positive)")
    styler.console.print("  Price: License price in dollars (required, defaults to 0)")
    styler.console.print("  Start Date: When license becomes active (required)")
    styler.console.print("  End Date: When license expires (optional)")

    # Prompt for license details
    name = typer.prompt("\nLicense name *", type=str)
    seats = typer.prompt("Number of seats *", type=int)

    # Validate seats
    while seats <= 0:
        styler.print_clean_message("Seats must be a positive number. Please try again.", MessageType.ERROR)
        seats = typer.prompt("Number of seats *", type=int)

    # Price (required, defaults to 0)
    price_input = typer.prompt("Price (USD, press Enter for 0)", default="0", show_default=True)
    price: Decimal = Decimal("0")
    try:
        price = Decimal(price_input)
        if price < 0:
            styler.print_clean_message("Price cannot be negative. Setting to 0.", MessageType.WARNING)
            price = Decimal("0")
    except Exception:
        styler.print_clean_message("Invalid price format. Using 0.", MessageType.WARNING)
        price = Decimal("0")

    # Start date (required)
    styler.console.print("\nStart date (format: YYYY-MM-DD, press Enter for today)")
    starts_at_input = typer.prompt("Start date", default="", show_default=False)
    starts_at: datetime
    if not starts_at_input:
        starts_at = datetime.now()
    else:
        try:
            starts_at = datetime.strptime(starts_at_input, "%Y-%m-%d")
        except ValueError:
            styler.print_clean_message("Invalid date format. Using today's date.", MessageType.WARNING)
            starts_at = datetime.now()

    # End date (optional)
    styler.console.print("\nEnd date (format: YYYY-MM-DD, press Enter to skip)")
    ends_at_input = typer.prompt("End date (optional)", default="", show_default=False)
    ends_at: Optional[datetime] = None
    if ends_at_input:
        try:
            ends_at = datetime.strptime(ends_at_input, "%Y-%m-%d")
            if ends_at <= starts_at:
                styler.print_clean_message("End date must be after start date. Skipping end date.", MessageType.WARNING)
                ends_at = None
        except ValueError:
            styler.print_clean_message("Invalid date format. Skipping end date.", MessageType.WARNING)
            ends_at = None

    # Optional description (stored in meta field)
    description = typer.prompt("\nDescription (optional, press Enter to skip)", default="", show_default=False)
    meta: Optional[dict] = None
    if description:
        meta = {"description": description}

    # Ask about activation using inquirer (following project pattern)
    styler.print_clean_message("Choose activation option for this license:", MessageType.INFO)
    styler.console.print("  1. Leave Inactive - License will not be active until manually activated")
    styler.console.print("  2. Activate Directly - Activate immediately without payment")
    styler.console.print("  3. Create Stripe Invoice - Send invoice and activate after payment")

    activation_choices = [
        inquirer.List(
            "activation",
            message="Select activation option",
            choices=[
                ("Leave Inactive (default)", "1"),
                ("Activate Directly (no payment)", "2"),
                ("Create Stripe Invoice (activate after payment)", "3"),
            ],
            default="1",
        )
    ]

    activation_answers = inquirer.prompt(activation_choices)
    activation_choice = activation_answers["activation"]

    styler.print_clean_message("Creating license...", MessageType.STEP)

    # Create license using the service
    async with with_default_db() as db:
        license_data = LicenseCreate(
            tenant_id=selected_tenant.tenant_id,
            name=name,
            seats=seats,
            price=price,
            starts_at=starts_at,
            ends_at=ends_at,
            status="inactive",
            meta=meta
        )

        try:
            license_obj = await license_service.create_license(db, license_data)
            license_id = license_obj.id
        except Exception as e:
            styler.print_clean_message(
                f"Failed to create license: {e!s}",
                MessageType.ERROR
            )
            raise

        # Handle activation based on choice
        if activation_choice == "2":
            # Direct activation (no payment)
            styler.print_clean_message("Activating license...", MessageType.STEP)
            try:
                await license_service.activate_license(db, license_id)
                # Refresh the license object to get updated status
                license_obj = await license_service.get_by_id(db, license_id)
                styler.print_clean_message("License activated successfully!", MessageType.SUCCESS)
            except Exception as e:
                styler.print_clean_message(
                    f"License created but activation failed: {e!s}",
                    MessageType.WARNING
                )

        elif activation_choice == "3":
            # Create Stripe invoice
            styler.print_clean_message("Creating Stripe invoice...", MessageType.STEP)
            try:
                result = await stripe_payment_service.process_invoice_flow(db, license_id)
                # Refresh the license object
                license_obj = await license_service.get_by_id(db, license_id)

                if result["code"] == "already_active":
                    styler.print_clean_message("License was already active!", MessageType.INFO)
                elif result["code"] == "activated":
                    styler.print_clean_message("Invoice paid! License activated!", MessageType.SUCCESS)
                elif result["code"] == "invoice_pending":
                    payload = result["payload"]
                    styler.print_clean_message("Stripe invoice created and sent!", MessageType.SUCCESS)
                    styler.console.print(f"  Invoice ID: {payload.get('invoice_id')}")
                    styler.console.print(f"  Hosted URL: {payload.get('hosted_invoice_url')}")
                    styler.console.print(f"  Status: {payload.get('status')}")
                elif result["code"] == "invoice_created":
                    payload = result["payload"]
                    styler.print_clean_message("Stripe invoice created and sent!", MessageType.SUCCESS)
                    styler.console.print(f"  Invoice ID: {payload.get('invoice_id')}")
                    styler.console.print(f"  Hosted URL: {payload.get('hosted_invoice_url')}")
            except Exception as e:
                styler.print_clean_message(
                    f"License created but Stripe invoice failed: {e!s}",
                    MessageType.WARNING
                )

        # Build table data while still in session context
        table_data = {
            "License ID": str(license_obj.id),
            "License Key": license_obj.license_key,
            "License Name": license_obj.name,
            "Tenant": selected_tenant.sub_domain,
            "Tenant ID": str(selected_tenant.tenant_id),
            "Seats": str(license_obj.seats),
            "Price": f"${license_obj.price:.2f}",
            "Status": license_obj.status,
            "Starts At": license_obj.starts_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

        if license_obj.ends_at:
            table_data["Ends At"] = license_obj.ends_at.strftime("%Y-%m-%d %H:%M:%S")

        if license_obj.meta and license_obj.meta.get("description"):
            table_data["Description"] = license_obj.meta["description"]

    # Display final summary (after session is closed)
    if activation_choice == "1":
        styler.print_clean_message("License created successfully (inactive)!", MessageType.SUCCESS)
    elif table_data["Status"] == "active":
        styler.print_clean_message("License created and activated!", MessageType.SUCCESS)
    else:
        styler.print_clean_message("License created!", MessageType.SUCCESS)

    styler.print_clean_table(table_data, "License Details")


def create_license():
    """Synchronous wrapper for the async create_license function."""
    asyncio.run(_create_license_async())


if __name__ == "__main__":
    create_license()
