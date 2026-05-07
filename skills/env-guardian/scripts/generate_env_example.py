#!/usr/bin/env python3
"""
generate_env_example.py - Generate .env.example and type-safe config loader.

Aggregates all discovered env vars, generates a comprehensive .env.example
with categorized variables and comments, and a Python config loader class.

Usage: python3 generate_env_example.py <project_dir> [--write]
  --write: Actually write the files (default: print to stdout)
Output: JSON with generated file contents to stdout
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# Import scan_env for reuse
sys.path.insert(0, str(Path(__file__).parent))
from scan_env import scan_project


# Category detection based on variable name patterns
CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("Database", [
        "DATABASE", "DB_", "POSTGRES", "MYSQL", "MONGO", "REDIS",
        "SQL", "SQLITE", "PGHOST", "PGPORT", "PGUSER", "PGPASS", "PGDATABASE",
    ]),
    ("Authentication", [
        "AUTH", "JWT", "SESSION", "OAUTH", "LOGIN", "SSO",
        "COOKIE", "CSRF",
    ]),
    ("API Keys & Secrets", [
        "API_KEY", "APIKEY", "SECRET", "TOKEN", "KEY",
        "PASSWORD", "PASSWD", "CREDENTIAL", "PRIVATE",
        "ACCESS_KEY", "SECRET_KEY",
    ]),
    ("AWS", [
        "AWS_", "S3_", "SQS_", "SNS_", "DYNAMO", "LAMBDA_",
    ]),
    ("Email", [
        "SMTP", "MAIL", "EMAIL", "SENDGRID", "MAILGUN",
    ]),
    ("Storage", [
        "STORAGE", "UPLOAD", "BUCKET", "CDN", "BLOB",
    ]),
    ("Logging & Monitoring", [
        "LOG", "SENTRY", "DATADOG", "NEWRELIC", "TRACE",
        "MONITOR", "DEBUG",
    ]),
    ("External Services", [
        "STRIPE", "TWILIO", "SLACK", "GITHUB", "GITLAB",
        "GOOGLE", "FACEBOOK", "TWITTER",
    ]),
    ("Application Config", [
        "APP_", "PORT", "HOST", "URL", "ENV", "NODE_ENV",
        "FLASK", "DJANGO", "RAILS", "NEXT_PUBLIC",
    ]),
]


def categorize_var(var_name: str) -> str:
    """Categorize an environment variable by its name."""
    upper = var_name.upper()
    for category, patterns in CATEGORY_RULES:
        for pattern in patterns:
            if pattern in upper:
                return category
    return "Other"


def infer_purpose(var_name: str) -> str:
    """Infer the purpose of a variable from its name."""
    upper = var_name.upper()
    hints = {
        "DATABASE_URL": "Full database connection URL",
        "DB_HOST": "Database server hostname",
        "DB_PORT": "Database server port",
        "DB_NAME": "Database name",
        "DB_USER": "Database username",
        "DB_PASSWORD": "Database password",
        "DB_SSL": "Enable SSL for database connection",
        "REDIS_URL": "Redis connection URL",
        "PORT": "Application listening port",
        "HOST": "Application hostname or bind address",
        "NODE_ENV": "Node.js environment (development/production/test)",
        "FLASK_ENV": "Flask environment mode",
        "DJANGO_SECRET_KEY": "Django cryptographic secret key",
        "SECRET_KEY": "Application secret key for signing",
        "JWT_SECRET": "Secret key for JWT token signing",
        "JWT_EXPIRY": "JWT token expiration time",
        "API_KEY": "API key for external service",
        "API_URL": "Base URL for API endpoint",
        "SMTP_HOST": "SMTP mail server hostname",
        "SMTP_PORT": "SMTP mail server port",
        "SMTP_USER": "SMTP authentication username",
        "SMTP_PASSWORD": "SMTP authentication password",
        "AWS_ACCESS_KEY_ID": "AWS access key ID",
        "AWS_SECRET_ACCESS_KEY": "AWS secret access key",
        "AWS_REGION": "AWS region",
        "S3_BUCKET": "AWS S3 bucket name",
        "SENTRY_DSN": "Sentry error tracking DSN",
        "LOG_LEVEL": "Logging level (debug/info/warn/error)",
        "DEBUG": "Enable debug mode (true/false)",
        "ALLOWED_HOSTS": "Comma-separated list of allowed hostnames",
        "CORS_ORIGINS": "Comma-separated list of allowed CORS origins",
    }

    if var_name in hints:
        return hints[var_name]

    # Generic inference
    if "URL" in upper:
        return f"URL for {var_name.lower().replace('_url', '').replace('_', ' ')}"
    if "HOST" in upper:
        return f"Hostname for {var_name.lower().replace('_host', '').replace('_', ' ')}"
    if "PORT" in upper:
        return f"Port number for {var_name.lower().replace('_port', '').replace('_', ' ')}"
    if "KEY" in upper or "SECRET" in upper or "TOKEN" in upper:
        return f"Secret/key for {var_name.lower().replace('_', ' ')}"
    if "PASSWORD" in upper or "PASSWD" in upper:
        return f"Password for {var_name.lower().replace('_password', '').replace('_passwd', '').replace('_', ' ')}"
    if "USER" in upper or "USERNAME" in upper:
        return f"Username for {var_name.lower().replace('_user', '').replace('_username', '').replace('_', ' ')}"
    if "ENABLED" in upper or "ENABLE" in upper:
        return f"Enable/disable {var_name.lower().replace('_enabled', '').replace('_enable', '').replace('_', ' ')}"
    if "PATH" in upper or "DIR" in upper:
        return f"File path for {var_name.lower().replace('_path', '').replace('_dir', '').replace('_', ' ')}"

    return f"Configuration for {var_name.lower().replace('_', ' ')}"


def infer_placeholder(var_name: str) -> str:
    """Infer a safe placeholder value for a variable."""
    upper = var_name.upper()

    if "URL" in upper and "DATABASE" in upper:
        return "postgresql://user:password@localhost:5432/dbname"
    if "REDIS" in upper and "URL" in upper:
        return "redis://localhost:6379/0"
    if "URL" in upper:
        return "https://example.com"
    if "HOST" in upper:
        return "localhost"
    if "PORT" in upper:
        return "3000"
    if upper in ("NODE_ENV", "FLASK_ENV", "APP_ENV", "ENVIRONMENT", "ENV"):
        return "development"
    if "DEBUG" in upper:
        return "false"
    if "LOG_LEVEL" in upper:
        return "info"
    if "REGION" in upper:
        return "us-east-1"
    if "SECRET" in upper or "KEY" in upper or "TOKEN" in upper or "PASSWORD" in upper:
        return "your-secret-here"
    if "USER" in upper:
        return "your-username"
    if "EMAIL" in upper:
        return "user@example.com"
    if "BUCKET" in upper:
        return "my-bucket-name"
    if "TRUE" in upper or "FALSE" in upper or "ENABLED" in upper:
        return "true"

    return ""


def is_required(var_name: str, scan_result: dict) -> bool:
    """Determine if a variable is likely required based on usage patterns."""
    # If it's used via os.environ['X'] (no default), it's required
    for ref in scan_result.get("references", []):
        if ref["variable"] == var_name:
            pattern = ref.get("pattern", "")
            # Direct access without default = required
            if pattern in ("os.environ['X']", "ENV['X']", "os.Getenv(\"X\")"):
                return True
            # process.env.X is ambiguous but treat as required
            if pattern == "process.env.X":
                return True
    return False


def generate_env_example(scan_result: dict) -> str:
    """Generate .env.example content."""
    # Collect all unique vars
    all_vars = set(scan_result.get("unique_variables", []))
    for env_file_vars in scan_result.get("env_files", {}).values():
        all_vars.update(env_file_vars)

    if not all_vars:
        return "# No environment variables discovered.\n"

    # Categorize
    categorized: dict[str, list[str]] = {}
    for var in sorted(all_vars):
        cat = categorize_var(var)
        categorized.setdefault(cat, []).append(var)

    # Generate content
    lines = [
        "# =============================================================================",
        "# Environment Variables Configuration",
        "# =============================================================================",
        "# Generated by env-guardian",
        "# Copy this file to .env and fill in the actual values.",
        "#",
        "# Variables marked [REQUIRED] must be set for the application to start.",
        "# Variables marked [OPTIONAL] have sensible defaults or are not critical.",
        "# =============================================================================",
        "",
    ]

    # Preferred category order
    category_order = [
        "Application Config", "Database", "Authentication",
        "API Keys & Secrets", "AWS", "Email", "Storage",
        "External Services", "Logging & Monitoring", "Other",
    ]

    ordered_cats = []
    for cat in category_order:
        if cat in categorized:
            ordered_cats.append(cat)
    for cat in sorted(categorized.keys()):
        if cat not in ordered_cats:
            ordered_cats.append(cat)

    for cat in ordered_cats:
        vars_in_cat = categorized[cat]
        lines.append(f"# --- {cat} ---")
        lines.append("")

        for var in vars_in_cat:
            purpose = infer_purpose(var)
            placeholder = infer_placeholder(var)
            required = is_required(var, scan_result)
            req_tag = "[REQUIRED]" if required else "[OPTIONAL]"

            lines.append(f"# {purpose} {req_tag}")
            lines.append(f"{var}={placeholder}")
            lines.append("")

    return "\n".join(lines)


def generate_config_loader(scan_result: dict) -> str:
    """Generate a type-safe Python config loader."""
    all_vars = set(scan_result.get("unique_variables", []))
    for env_file_vars in scan_result.get("env_files", {}).values():
        all_vars.update(env_file_vars)

    if not all_vars:
        return "# No environment variables discovered.\n"

    lines = [
        '"""',
        "Type-safe configuration loader.",
        "",
        "Generated by env-guardian.",
        "Import and use: from config import config",
        '"""',
        "",
        "import os",
        "from dataclasses import dataclass, field",
        "from typing import Optional",
        "",
        "",
        "def _get_env(key: str, default: Optional[str] = None, required: bool = False) -> str:",
        '    """Get environment variable with validation."""',
        "    value = os.environ.get(key, default)",
        "    if required and value is None:",
        '        raise EnvironmentError(',
        '            f"Required environment variable \'{key}\' is not set. "',
        '            f"Please add it to your .env file."',
        "        )",
        '    return value or ""',
        "",
        "",
        "def _get_bool(key: str, default: bool = False) -> bool:",
        '    """Get boolean environment variable."""',
        "    value = os.environ.get(key, str(default)).lower()",
        '    return value in ("true", "1", "yes", "on")',
        "",
        "",
        "def _get_int(key: str, default: int = 0) -> int:",
        '    """Get integer environment variable."""',
        "    try:",
        "        return int(os.environ.get(key, str(default)))",
        "    except ValueError:",
        "        return default",
        "",
        "",
        "@dataclass",
        "class Config:",
        '    """Application configuration loaded from environment variables."""',
        "",
    ]

    for var in sorted(all_vars):
        required = is_required(var, scan_result)
        purpose = infer_purpose(var)
        upper = var.upper()

        # Determine type
        if "PORT" in upper:
            type_str = "int"
            getter = f'_get_int("{var}", 3000)'
        elif "DEBUG" in upper or "ENABLED" in upper or "ENABLE" in upper:
            type_str = "bool"
            getter = f'_get_bool("{var}")'
        elif required:
            type_str = "str"
            getter = f'_get_env("{var}", required=True)'
        else:
            type_str = "str"
            placeholder = infer_placeholder(var)
            if placeholder:
                getter = f'_get_env("{var}", "{placeholder}")'
            else:
                getter = f'_get_env("{var}")'

        lines.append(f"    # {purpose}")
        lines.append(f"    {var}: {type_str} = field(default_factory=lambda: {getter})")
        lines.append("")

    lines.extend([
        "",
        "# Singleton instance - import this in your application",
        "config = Config()",
    ])

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_env_example.py <project_dir> [--write]", file=sys.stderr)
        sys.exit(1)

    project_dir = sys.argv[1]
    write_mode = "--write" in sys.argv

    scan_result = scan_project(project_dir)

    if "error" in scan_result:
        print(json.dumps(scan_result, indent=2))
        sys.exit(1)

    env_example = generate_env_example(scan_result)
    config_loader = generate_config_loader(scan_result)

    if write_mode:
        root = Path(project_dir).resolve()

        env_example_path = root / ".env.example.generated"
        env_example_path.write_text(env_example, encoding="utf-8")

        config_path = root / "config_generated.py"
        config_path.write_text(config_loader, encoding="utf-8")

        output = {
            "written_files": [str(env_example_path), str(config_path)],
            "env_example_vars": scan_result["unique_variable_count"],
        }
    else:
        output = {
            "env_example": env_example,
            "config_loader": config_loader,
            "total_vars": scan_result["unique_variable_count"],
        }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
