"""Security command module."""
import typer
from .generate import generate_encryption_key
from .generate import generate_jwt_keys
from .generate import generate_secret
from .validate import validate_keys

# Main security app
app = typer.Typer(help="Security and key management commands")

# Register all commands
app.command(name="validate-keys")(validate_keys)
app.command(name="generate-secret")(generate_secret)
app.command(name="generate-encryption-key")(generate_encryption_key)
app.command(name="generate-jwt-keys")(generate_jwt_keys)
