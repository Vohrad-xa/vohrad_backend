import functools
from alembic import op
from sqlalchemy import text
from typeguard import typechecked
from typing import Callable


@typechecked
def for_each_tenant_schema(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapped():
        try:
            result = op.get_bind().execute(text("SELECT tenant_schema_name FROM shared.tenants"))
            schemas = result.fetchall()
            for (schema,) in schemas:
                func(schema)
        except Exception:
            # If tenants table doesn't exist or has no data, create for default tenant schema
            func("tenant_default")

    return wrapped
