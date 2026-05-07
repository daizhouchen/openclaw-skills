> 📦 Part of [**openclaw-skills**](../../) monorepo
> Status: **experimental archive** · originally pushed 2026-03-31 ~ 2026-04-01
> One-liner: 环境变量审计 + .env.example 生成 — Audit env vars across languages

---

# env-guardian

> Protect your secrets. Audit your env vars. Never leak an API key again.

An [OpenClaw](https://openclaw.ai) skill that scans your project for environment variable usage across multiple languages, detects security vulnerabilities, validates configuration completeness, and generates a categorized `.env.example` with a type-safe Python config loader -- all without ever exposing a single secret value.

## Features

- Multi-language scanning across Python, JavaScript/TypeScript, Ruby, Go, Docker, CI/CD, and Docker Compose
- Security auditing with severity-ranked findings (CRITICAL / WARNING / INFO)
- Completeness analysis to find gaps between code references and `.env` definitions
- Automatic generation of `.env.example` and a typed Python `Config` dataclass
- Fully redacted output -- secret values never appear in reports

## Multi-Language Scanning

`scan_env.py` walks your project tree and matches env var references using language-specific regex patterns. The table below lists every pattern detected.

| Language / Context | Patterns Detected | File Extensions |
|--------------------|-------------------|-----------------|
| Python | `os.environ['X']`, `os.getenv('X')`, `os.environ.get('X')` | `.py` |
| JavaScript / TypeScript | `process.env.X`, `process.env['X']` | `.js`, `.jsx`, `.ts`, `.tsx`, `.mjs`, `.cjs` |
| Ruby | `ENV['X']`, `ENV.fetch('X')` | `.rb` |
| Go | `os.Getenv("X")`, `os.LookupEnv("X")` | `.go` |
| Dockerfile | `ENV X`, `ARG X`, `${X}` | `Dockerfile`, `Dockerfile.*` |
| GitHub Actions | `${{ secrets.X }}`, `${{ vars.X }}` | `.github/workflows/*.yml` |
| GitLab CI | `$X` | `.gitlab-ci.yml` |
| Docker Compose | `${X}`, `${X:-default}`, `X=` (under `environment:`) | `docker-compose.yml`, `docker-compose.yaml` |

Directories such as `node_modules`, `.git`, `__pycache__`, `.venv`, `vendor`, `dist`, `build`, `.next`, and `.nuxt` are automatically skipped.

## Security Checks

`check_security.py` runs four independent checks and tags every finding with a severity level.

| Check | Severity | What It Detects |
|-------|----------|-----------------|
| `.gitignore` audit | CRITICAL | `.env` exists but is not listed in `.gitignore`, or `.gitignore` is missing entirely |
| Git history scan | CRITICAL | `.env` was previously committed (uses `git log --all --diff-filter=A`) |
| Hardcoded secrets | CRITICAL | Assignments like `API_KEY = "sk-live-..."` in source code (scans `.py`, `.js`, `.ts`, `.rb`, `.go`, `.java`, `.php`, `.cs`, `.sh`, `.yml`, `.json`, `.toml`, `.cfg`, `.ini`, `.conf`) |
| Sensitive variable names | WARNING | Variables in `.env` files whose names contain `KEY`, `SECRET`, `PASSWORD`, `TOKEN`, `CREDENTIAL`, `PRIVATE`, `AUTH`, `ACCESS_KEY`, or `APIKEY` |

Placeholder values (`your_`, `changeme`, `example`, `dummy`, `test`, etc.) and env var references (`${...}`, `process.env`) are excluded from hardcoded-secret detection to reduce false positives.

## Completeness Analysis

The scanner cross-references three data sources to surface configuration gaps:

- **Missing from `.env` files** -- variables referenced in code but not defined in any `.env*` file
- **Defined but unused** -- variables present in `.env` files but never referenced in code
- **Missing from `.env.example`** -- variables in `.env` that have no counterpart in `.env.example` / `.env.sample` / `.env.template`

## Installation

```bash
npx @anthropic-ai/claw@latest skill add daizhouchen/env-guardian
```

## Quick Start

Once the skill is installed, ask OpenClaw to check your project. You can also run each script directly:

```bash
# Step 1 -- Scan all env var references (outputs JSON)
python3 scripts/scan_env.py /path/to/project

# Step 2 -- Run security audit (outputs JSON)
python3 scripts/check_security.py /path/to/project

# Step 3 -- Generate .env.example and config loader (preview)
python3 scripts/generate_env_example.py /path/to/project

# Step 3 (alt) -- Write generated files to disk
python3 scripts/generate_env_example.py /path/to/project --write
```

## How It Works

**`scripts/scan_env.py`** recursively walks the project tree, detects each file's language from its extension or filename, and applies the corresponding regex patterns. It also parses every `.env*` file (`.env`, `.env.local`, `.env.example`, etc.) to build a full variable inventory. Output is a JSON object containing all references with file paths, line numbers, and pattern types, plus gap analysis between code and `.env` files.

**`scripts/check_security.py`** performs four checks in sequence: `.gitignore` coverage, git history exposure, hardcoded secret scanning, and sensitive variable name detection. Every secret value is redacted through a `redact_value()` function that preserves only the first two and last two characters (e.g., `sk****3j`). Values four characters or shorter are fully masked as `****`.

**`scripts/generate_env_example.py`** imports `scan_env.scan_project()` to collect all discovered variables, then categorizes each one by name pattern (Database, Authentication, API Keys, AWS, Email, Storage, Logging, External Services, Application Config). It infers purpose descriptions and placeholder values, marks variables as `[REQUIRED]` or `[OPTIONAL]` based on access patterns, and produces two outputs: a `.env.example` file and a Python config loader module.

## Generated Outputs

### `.env.example`

```bash
# =============================================================================
# Environment Variables Configuration
# =============================================================================
# Generated by env-guardian
# Copy this file to .env and fill in the actual values.
# Variables marked [REQUIRED] must be set for the application to start.
# =============================================================================

# --- Database ---

# Full database connection URL [REQUIRED]
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# --- API Keys & Secrets ---

# Application secret key for signing [REQUIRED]
SECRET_KEY=your-secret-here
```

### Config Dataclass

```python
@dataclass
class Config:
    """Application configuration loaded from environment variables."""

    # Full database connection URL
    DATABASE_URL: str = field(default_factory=lambda: _get_env("DATABASE_URL", required=True))

    # Database server port
    DB_PORT: int = field(default_factory=lambda: _get_int("DB_PORT", 3000))

    # Enable debug mode (true/false)
    DEBUG: bool = field(default_factory=lambda: _get_bool("DEBUG"))

# Singleton instance - import this in your application
config = Config()
```

The module includes helpers `_get_env()`, `_get_bool()`, and `_get_int()` with validation. Required variables raise `EnvironmentError` when missing. With `--write`, files are saved as `.env.example.generated` and `config_generated.py` to avoid overwriting existing files.

## Security Principles

- Secret values are **never** included in any output -- scan results, security reports, or generated files
- The redaction format is `xx****xx` (first 2 + last 2 characters visible); values of 4 characters or fewer become `****`
- Reports contain only variable names, file locations, line numbers, and metadata
- Reports are safe to share with your team or paste into issues

## Trigger Phrases

The skill activates when the user mentions any of the following (Chinese and English):

| Language | Phrases |
|----------|---------|
| Chinese | "环境变量", ".env", "配置安全", "API key 泄露", "帮我检查一下配置有没有问题" |
| English | "environment variables", ".env", "config security", "secrets", "API key leak" |

## Project Structure

```
env-guardian/
├── SKILL.md                        # Skill definition and workflow instructions
├── README.md                       # This file
├── scripts/
│   ├── scan_env.py                 # Multi-language env var scanner
│   ├── check_security.py           # Security vulnerability checker
│   └── generate_env_example.py     # .env.example and config loader generator
├── assets/                         # Static assets
└── references/                     # Reference materials
```

## Example Report

```
Environment Variable Inventory
  Total unique variables: 14
  Scanned files: 87
  Total references: 42

  Missing from .env files:   SENTRY_DSN, REDIS_URL
  Defined but unused:        LEGACY_API_KEY

Security Findings
  CRITICAL  .env is NOT listed in .gitignore
  CRITICAL  Hardcoded secret: AWS_SECRET_KEY in deploy.py:23 (AK****9x)
  WARNING   Sensitive variable 'DB_PASSWORD' found in .env

Recommendations
  1. Add '.env' to .gitignore immediately
  2. Move 'AWS_SECRET_KEY' to .env and reference via os.environ
  3. Add SENTRY_DSN and REDIS_URL to your .env file
```

## Requirements

- Python 3.8+ (standard library only -- no external packages)
- Git (for history analysis in `check_security.py`)

## Limitations

- Regex-based detection may miss dynamically constructed variable names (e.g., `os.environ[prefix + "_KEY"]`)
- GitLab CI `$X` pattern can produce false positives on shell-style variable references in non-CI YAML files
- The config loader generator outputs Python only; other languages are not supported for code generation
- `.env` file parsing assumes simple `KEY=VALUE` format and does not handle multi-line values

## Contributing

Contributions welcome -- open an issue or submit a pull request. To add a new language, add patterns to the `PATTERNS` dict in `scan_env.py` and update `EXT_LANG_MAP`.

## License

MIT
