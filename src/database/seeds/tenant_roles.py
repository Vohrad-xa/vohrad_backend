"""Tenant role seeds for tenant schemas."""

import asyncio
from config.settings import get_settings
from constants.enums import RoleScope, RoleType
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4


def get_database_url():
    """Get database URL using the system's settings."""
    settings = get_settings()
    return f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"


TENANT_ROLES = [
    {
        "name"               : "manager",
        "description"        : "Tenant manager with delegated administration",
        "role_type"          : RoleType.PREDEFINED.name,
        "role_scope"         : RoleScope.TENANT.name,
        "managed_by"         : "manager",
        "permissions_mutable": False,
        "permissions"        : [
            ("tenant", "*"),
            ("role", "*"),
            ("permission", "*"),
            ("user", "create"),
            ("user", "read"),
            ("user", "update"),
            ("item", "*"),
            ("location", "*"),
        ],
    },
    {
        "name"               : "employee",
        "description"        : "Employee (basic tenant user)",
        "role_type"          : RoleType.PREDEFINED.name,
        "role_scope"         : RoleScope.TENANT.name,
        "permissions_mutable": True,
        "managed_by"         : "manager",
        "permissions"        : [],
    },
]


async def get_tenant_schemas():
    """Get list of tenant schemas from shared.tenants."""
    database_url = get_database_url()
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            result = await session.execute(
                sa.text("SELECT tenant_schema_name FROM shared.tenants WHERE tenant_schema_name != 'shared'")
            )
            schemas = [row[0] for row in result.fetchall()]
            await engine.dispose()
            return schemas
    except Exception as e:
        await engine.dispose()
        print(f"Could not get tenant schemas: {e}")
        return []


async def create_tenant_roles_for_schema(schema_name: str):
    """Create tenant roles for a specific schema."""
    database_url = get_database_url()
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            created_count = 0

            for role_config in TENANT_ROLES:
                quoted_schema = session.bind.dialect.identifier_preparer.quote_identifier(schema_name)
                result = await session.execute(
                    sa.text(f"SELECT id FROM {quoted_schema}.roles WHERE name = :name"), {"name": role_config["name"]}  # nosec B608
                )
                existing_role = result.scalar_one_or_none()

                if existing_role:
                    print(f"Role '{role_config['name']}' already exists in {schema_name}, updating permissions...")
                    role_id = existing_role

                    # Get existing permissions
                    perm_result = await session.execute(
                        sa.text(f"SELECT resource, action FROM {quoted_schema}.permissions WHERE role_id = :role_id"),  # nosec B608
                        {"role_id": role_id}
                    )
                    existing_perms = {(row[0], row[1]) for row in perm_result.fetchall()}

                    # Add missing permissions
                    added_count = 0
                    for resource, action in role_config["permissions"]:
                        if (resource, action) not in existing_perms:
                            await session.execute(
                                sa.text(f"""
                                    INSERT INTO {quoted_schema}.permissions (id, role_id, resource, action, created_at)
                                    VALUES (:id, :role_id, :resource, :action, :created_at)
                                """),  # nosec B608
                                {
                                    "id"        : str(uuid4()),
                                    "role_id"   : role_id,
                                    "resource"  : resource,
                                    "action"    : action,
                                    "created_at": datetime.now(),
                                },
                            )
                            added_count += 1

                    if added_count > 0:
                        print(f"  Added {added_count} new permissions to '{role_config['name']}'")
                    else:
                        print("  No new permissions to add")
                    continue

                role_id = str(uuid4())
                await session.execute(
                    sa.text(f"""
                        INSERT INTO {quoted_schema}.roles (id, name, description, role_type, role_scope,
                                                      stage, is_mutable, permissions_mutable, is_deletable,
                                                      managed_by, is_active, etag, created_at, updated_at)
                        VALUES (:id, :name, :description, :role_type, :role_scope,
                               :stage, :is_mutable, :permissions_mutable, :is_deletable,
                               :managed_by, :is_active, :etag, :created_at, :updated_at)
                    """),  # nosec B608
                    {
                        "id"                 : role_id,
                        "name"               : role_config["name"],
                        "description"        : role_config["description"],
                        "role_type"          : role_config["role_type"],
                        "role_scope"         : role_config["role_scope"],
                        "stage"              : "GA",
                        "is_mutable"         : False,
                        "permissions_mutable": role_config.get("permissions_mutable", False),
                        "is_deletable"       : False,
                        "managed_by"         : role_config.get("managed_by"),
                        "is_active"          : True,
                        "etag"               : "AA==",
                        "created_at"         : datetime.now(),
                        "updated_at"         : datetime.now(),
                    },
                )

                for resource, action in role_config["permissions"]:
                    await session.execute(
                        sa.text(f"""
                            INSERT INTO {quoted_schema}.permissions (id, role_id, resource, action, created_at)
                            VALUES (:id, :role_id, :resource, :action, :created_at)
                        """),  # nosec B608
                        {
                            "id"        : str(uuid4()),
                            "role_id"   : role_id,
                            "resource"  : resource,
                            "action"    : action,
                            "created_at": datetime.now(),
                        },
                    )

                created_count += 1
                print(f"Created role: {role_config['name']} in {schema_name}")

            await session.commit()
            return created_count

    except Exception as e:
        print(f"Error creating tenant roles for {schema_name}: {e}")
        return 0
    finally:
        await engine.dispose()


async def create_tenant_roles():
    """Create tenant roles for all tenant schemas."""
    tenant_schemas = await get_tenant_schemas()

    if not tenant_schemas:
        print("No tenant schemas found")
        return

    total_created = 0
    for schema_name in tenant_schemas:
        print(f"\nProcessing schema: {schema_name}")
        created = await create_tenant_roles_for_schema(schema_name)
        total_created += created

    print(f"\nCompleted! Created {total_created} tenant roles across {len(tenant_schemas)} schemas")


if __name__ == "__main__":
    asyncio.run(create_tenant_roles())
