"""Security command module."""

from .generate import generate_encryption_key, generate_jwt_keys, generate_secret
from .generate_token import app as token_app
from .permission_registry_cli import app as perm_registry_app
from .revoke_tokens import app as revoke_app
from .seed_global_roles import seed_global_roles
from .seed_tenant_roles import seed_tenant_roles
from .validate import validate_keys
import typer

# Main security app
app = typer.Typer(help="Security and key management commands")

# Register all commands
app.command(name="validate-keys")(validate_keys)
app.command(name="generate-secret")(generate_secret)
app.command(name="generate-encryption-key")(generate_encryption_key)
app.command(name="generate-jwt-keys")(generate_jwt_keys)
app.command(name="seed-global-roles")(seed_global_roles)
app.command(name="seed-tenant-roles")(seed_tenant_roles)
app.add_typer(token_app, name="token", help="JWT token generation for testing")
app.add_typer(revoke_app, name="revoke-tokens", help="JWT token revocation")
app.add_typer(perm_registry_app, name="perm-registry", help="Permission registry tools")
