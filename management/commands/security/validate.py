"""Security key validation commands."""

from commands import CLIStyler, MessageType
from config.keys import get_key_manager

styler = CLIStyler()


def validate_keys():
    """Validate application security keys and configuration."""
    styler.print_clean_header("Security Key Validation Report")

    key_manager = get_key_manager()
    status = key_manager.validate_keys()

    secret_configured = "Configured" if status["secret_key_configured"] else "Missing"
    secret_strength = f"({status['secret_key_strength']} - {status['secret_key_length']} chars)"

    enc_configured = "Configured" if status["encryption_key_configured"] else "Missing"

    env_style = "production" if status["environment"] == "production" else "development"

    table_data = {
        "secret_key": f"{secret_configured} {secret_strength}",
        "encryption_key": enc_configured,
        "jwt_algorithm": status["jwt_algorithm"],
        "environment": f"{status['environment']} ({env_style} mode)",
    }

    styler.print_clean_table(table_data, "Key Configuration Status")

    # Show warnings
    if status["warnings"]:
        styler.print_clean_header("Security Warnings")
        for warning in status["warnings"]:
            styler.print_clean_message(warning, MessageType.WARNING)
    else:
        styler.print_clean_message("No security warnings detected", MessageType.SUCCESS)

    # Security recommendations
    recommendations = []
    if status["environment"] == "production":
        if not status["secret_key_configured"]:
            recommendations.append("Configure a strong SECRET_KEY for production")
        elif status["secret_key_strength"] == "weak":
            recommendations.append("Use a stronger SECRET_KEY (64+ characters with special chars)")

        if not status["encryption_key_configured"]:
            recommendations.append("Consider setting a dedicated ENCRYPTION_KEY")

        recommendations.append("Regularly rotate security keys")
        recommendations.append("Use environment-specific key management")

    if recommendations:
        styler.print_clean_header("Security Recommendations")
        for rec in recommendations:
            print(f"  {rec}")
