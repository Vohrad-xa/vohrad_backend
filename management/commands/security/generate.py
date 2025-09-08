"""Security key generation commands."""

from commands import CLIEnvironment, CLIFileUtils, CLIStyler, MessageType
from config.keys import KeyManager
import os
from pathlib import Path
import typer

styler = CLIStyler()


def generate_secret(
    to_file: str = typer.Option(None, "--to-file", help="Write to specified file (e.g., .env.new)"),
    show: bool = typer.Option(False, "--show", help="Display key in console (development only)"),
):
    """Generate a new cryptographically secure secret key."""
    new_key = KeyManager.generate_secret_key()
    CLIFileUtils.handle_key_output("SECRET_KEY", new_key, to_file, show, styler=styler)


def generate_encryption_key(
    to_file: str = typer.Option(None, "--to-file", help="Write to specified file (e.g., .env.new)"),
    show: bool = typer.Option(False, "--show", help="Display key in console (development only)"),
):
    """Generate a new base64-encoded encryption key."""
    new_key = KeyManager.generate_encryption_key()
    CLIFileUtils.handle_key_output("ENCRYPTION_KEY", new_key, to_file, show, styler=styler)


def generate_jwt_keys(
    to_dir: str = typer.Option("keys", "--to-dir", help="Directory to save keys (default: keys/)"),
    show: bool = typer.Option(False, "--show", help="Display keys in console (development only)"),
):
    """Generate RSA key pair for JWT signing with production-safe output."""
    env = CLIEnvironment.get_environment()
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
    os.chmod(public_key_path, 0o644)  # Public key: readable

    styler.print_clean_message("RSA key pair generated successfully", MessageType.SUCCESS)

    # Display key file information using clean table
    key_info = {"Private Key": f"{private_key_path} (permissions: 600)", "Public Key": f"{public_key_path} (permissions: 644)"}
    styler.print_clean_table(key_info, "Generated Key Files")

    # Environment-specific display behavior
    if show and env == "development":
        styler.console.print("\nPrivate Key (development display only):")
        styler.console.print(private_key)
        styler.console.print("\nPublic Key:")
        styler.console.print(public_key)
        styler.print_clean_message("Clear terminal history after viewing", MessageType.WARNING)
    elif env == "production":
        styler.print_clean_message("Production mode: Keys saved securely, not displayed", MessageType.INFO)
        styler.console.print("Use --show flag in development only")
    else:
        styler.console.print("Use --show flag to display keys (development only)")

    # Display next steps
    styler.print_clean_header("Next Steps")
    styler.console.print(f"  Update JWT_PRIVATE_KEY_PATH={private_key_path}")
    styler.console.print(f"  Update JWT_PUBLIC_KEY_PATH={public_key_path}")
    styler.console.print("  Add these paths to your .env file")
