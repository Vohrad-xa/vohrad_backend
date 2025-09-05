"""Tenant creation commands."""

import alembic
from alembic.config import Config
from alembic.migration import MigrationContext
import alembic.script
from api.tenant.models import Tenant
import asyncio
from commands import CLIStyler, MessageType
from database import Base
from database.sessions import with_default_db
import sqlalchemy as sa
import typer

styler = CLIStyler()


def create_tenant():
    """Create a new tenant in the shared schema tenants table and create the schema in the database."""
    styler.print_clean_header("Tenant Creation")

    styler.print_clean_message("Please provide the following tenant details:", MessageType.INFO)
    styler.console.print("Schema name: Database schema identifier (lowercase, no spaces)")
    styler.console.print("Subdomain: Tenant's subdomain (e.g., company1 for company1.example.com)")
    styler.console.print("Email: Contact email for the tenant (required)")

    schema_name = typer.prompt("\nSchema name *", type=str)
    sub_domain  = typer.prompt("Subdomain *", type=str)
    email       = typer.prompt("Email *", type=str)

    styler.console.print("\nOptional information (press Enter to skip):")
    telephone = typer.prompt("Telephone", default="", show_default=False)
    website   = typer.prompt("Website", default="", show_default=False)
    industry  = typer.prompt("Industry", default="", show_default=False)
    city      = typer.prompt("City", default="", show_default=False)
    country   = typer.prompt("Country", default="", show_default=False)

    styler.print_clean_message("Creating tenant and database schema...", MessageType.INFO)

    asyncio.run(_create_tenant(schema_name, sub_domain, email, telephone, website, industry, city, country))

    table_data = {
        "Schema Name": schema_name,
        "Subdomain"  : sub_domain,
        "Email"      : email,
        "Status"     : "Active"
    }
    if telephone:
        table_data["Telephone"] = telephone
    if website:
        table_data["Website"] = website
    if industry:
        table_data["Industry"] = industry
    if city:
        table_data["City"] = city
    if country:
        table_data["Country"] = country

    styler.print_clean_table(table_data, "Tenant Details")
    styler.print_clean_message("Tenant created successfully!", MessageType.SUCCESS)


async def _create_tenant(
    schema_name: str,
    sub_domain : str,
    email      : str,
    telephone  : str | None = None,
    website    : str | None = None,
    industry   : str | None = None,
    city       : str | None = None,
    country    : str | None = None,
) -> None:
    """Create a new tenant in the shared schema tenants table and create the schema in the database.

    1. check if the database is up-to-date with migrations.
    2. add the new tenant.
    3. create the schema in the database.
    4. commit the transaction."""
    async with with_default_db() as db:
        connection = await db.connection()

        def check_migrations_sync(sync_conn):
            alembic_cfg = Config("alembic.ini")
            migration_context = MigrationContext.configure(sync_conn)
            current_revision = migration_context.get_current_revision()

            script_directory = alembic.script.ScriptDirectory.from_config(alembic_cfg)
            head_revision = script_directory.get_current_head()

            if current_revision != head_revision:
                styler.print_clean_message(
                    f"Database is not up-to-date. Current revision: {current_revision}, "
                    f"Head revision: {head_revision}. Please run migrations first.",
                    MessageType.ERROR)
                raise RuntimeError(
                    f"Database is not up-to-date. Current revision: {current_revision}, "
                    f"Head revision: {head_revision}. Please run migrations first."
                )

        await connection.run_sync(check_migrations_sync)

        tenant = Tenant(
            sub_domain         = sub_domain,
            tenant_schema_name = schema_name,
            email              = email,
            status             = "active",
            telephone          = telephone or None,
            website            = website or None,
            industry           = industry or None,
            city               = city or None,
            country            = country or None,
        )
        db.add(tenant)
        await db.commit()
        await db.execute(sa.schema.CreateSchema(schema_name))
        await db.commit()

    """create tables in tenant schema."""
    from database.engine import async_engine

    def create_tables_sync(sync_conn):
        tenant_metadata = get_tenant_specific_metadata()
        tenant_metadata.create_all(bind=sync_conn, checkfirst=True)

    engine_with_schema = async_engine.execution_options(schema_translate_map={"tenant_default": schema_name})
    async with engine_with_schema.begin() as conn:
        await conn.run_sync(create_tables_sync)


def get_tenant_specific_metadata():
    meta = sa.MetaData()

    for table in Base.metadata.tables.values():
        if table.schema == "shared":
            table.tometadata(meta)

    for table in Base.metadata.tables.values():
        if table.schema != "shared":
            table.tometadata(
                meta,
                referred_schema_fn=lambda table, to_schema, constraint, referred_schema: (
                    referred_schema or to_schema
                ),
            )
    return meta
