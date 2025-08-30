"""Security key generation commands."""
import os
import sys
import typer
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root / "src"))
os.chdir(project_root)

from .utils import console  # noqa: E402
from .utils import get_environment  # noqa: E402
from .utils import handle_key_output  # noqa: E402
from config.keys import KeyManager  # noqa: E402


def generate_secret(
    to_file: str = typer.Option(None, "--to-file", help="Write to specified file (e.g., .env.new)"),
    show: bool = typer.Option(False, "--show", help="Display key in console (development only)")
):
    """Generate a new cryptographically secure secret key."""
    new_key = KeyManager.generate_secret_key()
    handle_key_output("SECRET_KEY", new_key, to_file, show)


def generate_encryption_key(
    to_file: str = typer.Option(None, "--to-file", help="Write to specified file (e.g., .env.new)"),
    show: bool = typer.Option(False, "--show", help="Display key in console (development only)")
):
    """Generate a new base64-encoded encryption key."""
    new_key = KeyManager.generate_encryption_key()
    handle_key_output("ENCRYPTION_KEY", new_key, to_file, show)


def generate_jwt_keys(
    to_dir: str = typer.Option("keys", "--to-dir", help="Directory to save keys (default: keys/)"),
    show: bool = typer.Option(False, "--show", help="Display keys in console (development only)")
):
    """Generate RSA key pair for JWT signing with production-safe output."""
    env = get_environment()
    private_key, public_key = KeyManager.generate_rsa_key_pair()

    # Ensure keys directory exists
    keys_dir = Path(to_dir)
    keys_dir.mkdir(exist_ok=True)

    # Write keys to files with secure permissions
    private_key_path = keys_dir / "jwt_private.pem"
    public_key_path = keys_dir / "jwt_public.pem"

    with open(private_key_path, "w", encoding="utf-8") as f:
        f.write(private_key)
    with open(public_key_path, "w", encoding="utf-8") as f:
        f.write(public_key)

    # Set secure file permissions
    os.chmod(private_key_path, 0o600)  # Private key: owner-only
    os.chmod(public_key_path, 0o644)   # Public key: readable

    console.print("[bold green][SUCCESS] RSA key pair generated successfully[/bold green]")
    console.print(f"[yellow]Private key: {private_key_path} (permissions: 600)[/yellow]")
    console.print(f"[yellow]Public key: {public_key_path} (permissions: 644)[/yellow]")
    console.print()

    # Environment-specific display behavior
    if show and env == "development":
        console.print("[bold blue]Private Key (development display only):[/bold blue]")
        console.print(f"[dim]{private_key}[/dim]")
        console.print()
        console.print("[bold blue]Public Key:[/bold blue]")
        console.print(f"[dim]{public_key}[/dim]")
        console.print()
        console.print("[red]Warning: Clear terminal history after viewing[/red]")
    elif env == "production":
        console.print("[dim]Production mode: Keys saved securely, not displayed[/dim]")
        console.print("[dim]Use --show flag in development only[/dim]")
    else:
        console.print("[yellow]Use --show flag to display keys (development only)[/yellow]")

    console.print()
    console.print("[bold blue]Next steps:[/bold blue]")
    console.print(f"  • Update JWT_PRIVATE_KEY_PATH={private_key_path}")
    console.print(f"  • Update JWT_PUBLIC_KEY_PATH={public_key_path}")
    console.print("  • Add these paths to your .env file")
