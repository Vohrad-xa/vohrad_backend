import asyncio
from typing import Annotated
import alembic
import alembic.script
import sqlalchemy as sa
import typer
from alembic.config import Config
from alembic.migration import MigrationContext
from api.tenant.models import Tenant
from database import Base
from database.sessions import with_default_db

app = typer.Typer()

@app.command(name="create_tenant")
def create_tenant(
    schema_name: Annotated[
        str, typer.Option("--schema-name", "-s", help="The name of the schema for the tenant in the database.")
    ],
    sub_domain: Annotated[
        str, typer.Option("--sub-domain", "-d", help="The subdomain for the tenant. example: tenant1.example.com")
    ],
):
    """Create a new tenant in the shared schema tenants table and create the schema in the database."""
    typer.echo(" Creating a new tenant")
    asyncio.run(_create_tenant(schema_name, sub_domain))
    typer.echo(" Tenant created successfully")

async def _create_tenant(schema_name: str, sub_domain: str) -> None:
    """Create a new tenant in the shared schema tenants table and create the schema in the database.
    1. check if the database is up-to-date with migrations.
    2. add the new tenant.
    3. create the schema in the database.
    4. commit the transaction.
    """
    async with with_default_db() as db:
        connection = await db.connection()

        def check_migrations_sync(sync_conn):
            alembic_cfg = Config("alembic.ini")
            migration_context = MigrationContext.configure(sync_conn)
            current_revision = migration_context.get_current_revision()

            script_directory = alembic.script.ScriptDirectory.from_config(alembic_cfg)
            head_revision = script_directory.get_current_head()

            if current_revision != head_revision:
                raise RuntimeError(
                    f"Database is not up-to-date. Current revision: {current_revision}, "
                    f"Head revision: {head_revision}. Please run migrations first."
                )

        await connection.run_sync(check_migrations_sync)

        tenant = Tenant(
            sub_domain=sub_domain,
            tenant_schema_name=schema_name,
            status="active",
        )
        db.add(tenant)
        await db.commit()
        await db.execute(sa.schema.CreateSchema(schema_name))
        await db.commit()

    """create tables in tenant schema."""
    from database.engine import async_engine

    def create_tables_sync(sync_conn):
        tables_to_create = [table for table in Base.metadata.tables.values() if table.schema != "shared"]
        for table in tables_to_create:
            table.create(bind=sync_conn, checkfirst=True)

    engine_with_schema = async_engine.execution_options(schema_translate_map={"tenant_default": schema_name})
    async with engine_with_schema.begin() as conn:
        await conn.run_sync(create_tables_sync)

def get_tenant_specific_metadata():
    meta = sa.MetaData()
    for table in Base.metadata.tables.values():
        if table.schema != "shared":
            table.tometadata(
                meta,
                referred_schema_fn=lambda table, to_schema, constraint, **kw: constraint.referred_table.schema
                or to_schema,
            )
    return meta
