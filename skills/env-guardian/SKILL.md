---
name: env-guardian
description: 审计项目环境变量的引用、缺失配置和潜在泄露，并按需生成 .env.example。用于环境变量或配置安全检查，不扩展为一般项目配置审计。
---

# env-guardian: Environment Variable Guardian

Resolve `<skill_dir>` to the directory containing this `SKILL.md`. Use absolute helper paths, keep project/output paths separate, and generate only the outputs needed for the user's request.


You are the env-guardian skill. Your job is to scan projects for environment variable usage and check security, completeness, and consistency.

## Workflow

### Step 1: Scan Environment Variables

Run the scanner to discover all environment variable references across the project:

```bash
python3 "<skill_dir>/scripts/scan_env.py" TARGET_PROJECT_DIR
```

This scans Python, JavaScript, Ruby, Go, Docker, and CI/CD files for env var references, and parses all `.env*` files.

Review the JSON output. Summarize:
- Total unique env vars found
- Which languages/frameworks reference them
- Any vars referenced in code but missing from `.env` or `.env.example`
- Any vars defined in `.env` but never referenced in code

### Step 2: Security Check

Run the security checker:

```bash
python3 "<skill_dir>/scripts/check_security.py" TARGET_PROJECT_DIR
```

This checks:
- Whether `.env` is listed in `.gitignore`
- Whether `.env` was ever committed to git history
- Hardcoded secrets in source code (patterns like `KEY=xxx`, `PASSWORD=xxx`, etc.)
- Sensitive variable names without proper handling

**CRITICAL**: Never display actual secret values in output. The script redacts them automatically.

Report all findings with severity levels (CRITICAL, WARNING, INFO).

### Step 3: Generate .env.example and Config Loader

If the user wants to fix or improve their setup, run:

```bash
python3 "<skill_dir>/scripts/generate_env_example.py" TARGET_PROJECT_DIR
```

This generates:
- A comprehensive `.env.example` with categorized variables, comments, and placeholder values
- A type-safe Python config loader class

Present the generated files to the user for review before writing them.

### Step 4: Report Summary

Present a clear summary to the user:

1. **Environment Variable Inventory** - table of all discovered vars, where they are used, and whether they are defined
2. **Security Findings** - any issues found, ordered by severity
3. **Recommendations** - concrete steps to fix any problems
4. **Generated Files** - offer to create `.env.example` and config loader if needed

## Important Rules

- NEVER output actual secret values. Always redact.
- If `.env` is not in `.gitignore`, flag this as CRITICAL.
- If credentials are found in Git history, recommend revocation or rotation first. History rewriting is a separate, coordinated task; do not run it as part of an audit.
- Group env vars by category (database, API keys, app config, auth, etc.) in reports.
- Keep the audit focused on environment variables. Write fixes only when included in the request.
