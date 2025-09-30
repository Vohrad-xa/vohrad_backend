"""Global role seeds for shared schema."""

import asyncio
from config.settings import get_settings
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4


def get_database_url():
    """Get database URL using the system's settings."""
    settings = get_settings()
    return f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"


GLOBAL_ROLES = [
    {
        "name"       : "super_admin",
        "description": "Complete system access across all tenants",
        "role_type"  : "BASIC",
        "role_scope" : "GLOBAL",
        "permissions": [("*", "*")],
    },
    {
        "name"       : "admin",
        "description": "Administrative access with tenant management",
        "role_type"  : "BASIC",
        "role_scope" : "GLOBAL",
        "permissions": [("tenant", "*"), ("user", "*"), ("system", "read")],
    },
]


async def create_global_roles():
    """Create global roles in shared schema."""
    database_url = get_database_url()

    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            created_count = 0

            for role_config in GLOBAL_ROLES:
                # Check if role already exists
                result = await session.execute(
                    sa.text("SELECT COUNT(*) FROM shared.roles WHERE name = :name"), {"name": role_config["name"]}
                )
                exists = result.scalar() > 0

                if exists:
                    print(f"Role '{role_config['name']}' already exists, skipping...")
                    continue

                # Create role
                role_id = str(uuid4())
                await session.execute(
                    sa.text("""
                        INSERT INTO shared.roles (id, name, description, role_type, role_scope,
                                                stage, is_mutable, permissions_mutable, is_deletable,
                                                is_active, created_at, updated_at)
                        VALUES (:id, :name, :description, :role_type, :role_scope,
                               :stage, :is_mutable, :permissions_mutable, :is_deletable,
                               :is_active, :created_at, :updated_at)
                    """),
                    {
                        "id"                 : role_id,
                        "name"               : role_config["name"],
                        "description"        : role_config["description"],
                        "role_type"          : role_config["role_type"],
                        "role_scope"         : role_config["role_scope"],
                        "stage"              : "GA",
                        "is_mutable"         : False,
                        "permissions_mutable": False,
                        "is_deletable"       : False,
                        "is_active"          : True,
                        "created_at"         : datetime.now(),
                        "updated_at"         : datetime.now(),
                    },
                )

                # Create permissions
                for resource, action in role_config["permissions"]:
                    await session.execute(
                        sa.text("""
                            INSERT INTO shared.permissions (id, role_id, resource, action, created_at)
                            VALUES (:id, :role_id, :resource, :action, :created_at)
                        """),
                        {
                            "id"        : str(uuid4()),
                            "role_id"   : role_id,
                            "resource"  : resource,
                            "action"    : action,
                            "created_at": datetime.now(),
                        },
                    )

                created_count += 1
                print(f"Created role: {role_config['name']}")

            await session.commit()

            if created_count > 0:
                print(f"Successfully created {created_count} global roles")
            else:
                print("No new roles were created")

    except Exception as e:
        print(f"Error creating global roles: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_global_roles())
