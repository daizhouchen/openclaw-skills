#!/usr/bin/env python3
"""
check_security.py - Environment variable security checker.

Checks for:
- .env in .gitignore
- Hardcoded secrets in code
- .env commits in git history
- Sensitive variable name detection

CRITICAL: Never outputs actual secret values.

Usage: python3 check_security.py <project_dir>
Output: JSON to stdout
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


# Sensitive variable name patterns
SENSITIVE_PATTERNS = [
    "KEY", "SECRET", "PASSWORD", "PASSWD", "TOKEN", "CREDENTIAL",
    "API_KEY", "APIKEY", "PRIVATE", "AUTH", "ACCESS_KEY",
]

# Hardcoded secret patterns in source code
# These match assignments like: API_KEY = "actual_value"
HARDCODED_SECRET_PATTERNS = [
    # Generic: SOME_KEY = "value" or SOME_KEY = 'value'
    re.compile(
        r"""(?:^|[\s;,])"""
        r"""([A-Za-z_]*(?:"""
        + "|".join(SENSITIVE_PATTERNS)
        + r""")[A-Za-z_0-9]*)"""
        r"""\s*[=:]\s*['"]([^'"]{8,})['"]""",
        re.IGNORECASE,
    ),
    # JavaScript const/let/var: const API_KEY = "value"
    re.compile(
        r"""(?:const|let|var)\s+([A-Za-z_]*(?:"""
        + "|".join(SENSITIVE_PATTERNS)
        + r""")[A-Za-z_0-9]*)\s*=\s*['"]([^'"]{8,})['"]""",
        re.IGNORECASE,
    ),
]

# File extensions to scan for hardcoded secrets
CODE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".rb", ".go", ".java",
    ".php", ".cs", ".sh", ".bash", ".yml", ".yaml", ".json",
    ".toml", ".cfg", ".ini", ".conf",
}

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "vendor", ".tox", ".mypy_cache", ".pytest_cache", "dist",
    "build", ".next", ".nuxt",
}


def redact_value(value: str) -> str:
    """Redact a secret value, showing only length hint."""
    if len(value) <= 4:
        return "****"
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def check_gitignore(project_dir: Path) -> list[dict[str, Any]]:
    """Check if .env is in .gitignore."""
    findings = []
    gitignore_path = project_dir / ".gitignore"
    env_path = project_dir / ".env"

    if not env_path.exists():
        findings.append({
            "severity": "INFO",
            "type": "no_env_file",
            "message": "No .env file found in project root.",
        })
        return findings

    if not gitignore_path.exists():
        findings.append({
            "severity": "CRITICAL",
            "type": "no_gitignore",
            "message": "No .gitignore file found! .env file is at risk of being committed.",
            "recommendation": "Create a .gitignore file and add '.env' to it.",
        })
        return findings

    try:
        gitignore_content = gitignore_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return findings

    # Check for .env entries in gitignore
    env_ignored = False
    for line in gitignore_content.splitlines():
        line = line.strip()
        if line in (".env", ".env*", ".env.*", "*.env"):
            env_ignored = True
            break
        # Also check for patterns like .env.local etc.
        if line.startswith(".env"):
            env_ignored = True
            break

    if not env_ignored:
        findings.append({
            "severity": "CRITICAL",
            "type": "env_not_in_gitignore",
            "message": ".env file exists but is NOT listed in .gitignore!",
            "recommendation": "Add '.env' to your .gitignore immediately.",
        })
    else:
        findings.append({
            "severity": "INFO",
            "type": "env_in_gitignore",
            "message": ".env is properly listed in .gitignore.",
        })

    return findings


def check_git_history(project_dir: Path) -> list[dict[str, Any]]:
    """Check if .env was ever committed to git history."""
    findings = []

    git_dir = project_dir / ".git"
    if not git_dir.exists():
        findings.append({
            "severity": "INFO",
            "type": "no_git_repo",
            "message": "Not a git repository. Cannot check history.",
        })
        return findings

    try:
        result = subprocess.run(
            ["git", "log", "--all", "--diff-filter=A", "--name-only", "--pretty=format:", "--", ".env"],
            capture_output=True, text=True, cwd=project_dir, timeout=10,
        )
        output = result.stdout.strip()
        if output:
            findings.append({
                "severity": "CRITICAL",
                "type": "env_in_git_history",
                "message": ".env file was previously committed to git history!",
                "recommendation": (
                    "Secrets may be exposed in git history. "
                    "Use 'git filter-branch' or BFG Repo-Cleaner to remove it, "
                    "then rotate ALL secrets that were in the file."
                ),
            })
        else:
            findings.append({
                "severity": "INFO",
                "type": "env_not_in_history",
                "message": ".env file has not been found in git commit history.",
            })
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        findings.append({
            "severity": "WARNING",
            "type": "git_check_failed",
            "message": f"Could not check git history: {e}",
        })

    return findings


def check_hardcoded_secrets(project_dir: Path) -> list[dict[str, Any]]:
    """Scan code for hardcoded secrets."""
    findings = []
    seen = set()  # Deduplicate by (file, line, variable)

    for dirpath, dirnames, filenames in os.walk(project_dir):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for filename in filenames:
            filepath = Path(dirpath) / filename

            # Skip non-code files and .env files
            if filepath.suffix not in CODE_EXTENSIONS:
                continue
            if filename.startswith(".env"):
                continue

            try:
                content = filepath.read_text(encoding="utf-8", errors="replace")
            except (OSError, PermissionError):
                continue

            lines = content.splitlines()
            for line_num, line in enumerate(lines, 1):
                # Skip comments
                stripped = line.strip()
                if stripped.startswith(("#", "//", "*", "/*")):
                    continue

                for pattern in HARDCODED_SECRET_PATTERNS:
                    for match in pattern.finditer(line):
                        var_name = match.group(1)
                        raw_value = match.group(2)

                        # Skip obvious placeholders
                        placeholders = [
                            "your_", "xxx", "changeme", "placeholder",
                            "example", "replace", "todo", "fixme",
                            "insert", "dummy", "test", "fake", "sample",
                        ]
                        if any(p in raw_value.lower() for p in placeholders):
                            continue
                        # Skip env var references
                        if raw_value.startswith("${") or raw_value.startswith("process.env"):
                            continue

                        rel_path = str(filepath.relative_to(project_dir))
                        dedup_key = (rel_path, line_num, var_name)
                        if dedup_key in seen:
                            continue
                        seen.add(dedup_key)
                        findings.append({
                            "severity": "CRITICAL",
                            "type": "hardcoded_secret",
                            "variable": var_name,
                            "file": rel_path,
                            "line": line_num,
                            "value_hint": redact_value(raw_value),
                            "message": f"Hardcoded secret found: {var_name} in {rel_path}:{line_num}",
                            "recommendation": (
                                f"Move '{var_name}' to .env file and reference it via environment variable."
                            ),
                        })

    return findings


def check_sensitive_vars(project_dir: Path) -> list[dict[str, Any]]:
    """Check for sensitive variable names in .env files and warn."""
    findings = []

    for dirpath, dirnames, filenames in os.walk(project_dir):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for filename in filenames:
            if not filename.startswith(".env"):
                continue
            if "example" in filename or "sample" in filename or "template" in filename:
                continue

            filepath = Path(dirpath) / filename
            try:
                content = filepath.read_text(encoding="utf-8", errors="replace")
            except (OSError, PermissionError):
                continue

            for line_num, line in enumerate(content.splitlines(), 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("export "):
                    line = line[7:]

                match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line)
                if not match:
                    continue

                var_name = match.group(1)
                upper_name = var_name.upper()
                for sensitive in SENSITIVE_PATTERNS:
                    if sensitive in upper_name:
                        rel_path = str(filepath.relative_to(project_dir))
                        findings.append({
                            "severity": "WARNING",
                            "type": "sensitive_var_in_env",
                            "variable": var_name,
                            "file": rel_path,
                            "line": line_num,
                            "message": (
                                f"Sensitive variable '{var_name}' found in {rel_path}. "
                                f"Ensure this file is not committed to version control."
                            ),
                        })
                        break

    return findings


def run_security_check(project_dir: str) -> dict[str, Any]:
    """Run all security checks."""
    root = Path(project_dir).resolve()
    if not root.is_dir():
        return {"error": f"Directory not found: {project_dir}"}

    all_findings: list[dict[str, Any]] = []

    all_findings.extend(check_gitignore(root))
    all_findings.extend(check_git_history(root))
    all_findings.extend(check_hardcoded_secrets(root))
    all_findings.extend(check_sensitive_vars(root))

    # Summary counts
    severity_counts = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
    for f in all_findings:
        sev = f.get("severity", "INFO")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    return {
        "project_dir": str(root),
        "total_findings": len(all_findings),
        "severity_counts": severity_counts,
        "findings": all_findings,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 check_security.py <project_dir>", file=sys.stderr)
        sys.exit(1)

    project_dir = sys.argv[1]
    result = run_security_check(project_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
