#!/usr/bin/env python3
"""
scan_env.py - Multi-language environment variable reference scanner.

Scans a project directory for environment variable references across
Python, JavaScript, Ruby, Go, Docker, and CI/CD configuration files.
Also parses .env, .env.example, and .env.* files.

Usage: python3 scan_env.py <project_dir>
Output: JSON to stdout
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any


# Regex patterns for env var references by language/context
PATTERNS: dict[str, list[tuple[re.Pattern, str]]] = {
    "python": [
        (re.compile(r"""os\.environ\[['"]([A-Za-z_][A-Za-z0-9_]*)['"]"""), "os.environ['X']"),
        (re.compile(r"""os\.getenv\(\s*['"]([A-Za-z_][A-Za-z0-9_]*)['"]"""), "os.getenv('X')"),
        (re.compile(r"""os\.environ\.get\(\s*['"]([A-Za-z_][A-Za-z0-9_]*)['"]"""), "os.environ.get('X')"),
    ],
    "javascript": [
        (re.compile(r"""process\.env\.([A-Za-z_][A-Za-z0-9_]*)"""), "process.env.X"),
        (re.compile(r"""process\.env\[['"]([A-Za-z_][A-Za-z0-9_]*)['"]"""), "process.env['X']"),
    ],
    "ruby": [
        (re.compile(r"""ENV\[['"]([A-Za-z_][A-Za-z0-9_]*)['"]"""), "ENV['X']"),
        (re.compile(r"""ENV\.fetch\(\s*['"]([A-Za-z_][A-Za-z0-9_]*)['"]"""), "ENV.fetch('X')"),
    ],
    "go": [
        (re.compile(r"""os\.Getenv\(\s*"([A-Za-z_][A-Za-z0-9_]*)"\s*\)"""), "os.Getenv(\"X\")"),
        (re.compile(r"""os\.LookupEnv\(\s*"([A-Za-z_][A-Za-z0-9_]*)"\s*\)"""), "os.LookupEnv(\"X\")"),
    ],
    "docker": [
        (re.compile(r"""^\s*ENV\s+([A-Za-z_][A-Za-z0-9_]*)""", re.MULTILINE), "ENV X"),
        (re.compile(r"""^\s*ARG\s+([A-Za-z_][A-Za-z0-9_]*)""", re.MULTILINE), "ARG X"),
        (re.compile(r"""\$\{([A-Za-z_][A-Za-z0-9_]*)\}"""), "${X}"),
    ],
    "github_actions": [
        (re.compile(r"""\$\{\{\s*secrets\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}"""), "${{ secrets.X }}"),
        (re.compile(r"""\$\{\{\s*vars\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}"""), "${{ vars.X }}"),
    ],
    "gitlab_ci": [
        (re.compile(r"""\$([A-Za-z_][A-Za-z0-9_]*)"""), "$X (GitLab CI)"),
    ],
    "docker_compose": [
        (re.compile(r"""\$\{([A-Za-z_][A-Za-z0-9_]*)(?::?-[^}]*)?\}"""), "${X} (compose)"),
        (re.compile(r"""^\s*-\s*([A-Za-z_][A-Za-z0-9_]*)=""", re.MULTILINE), "X= (compose env)"),
    ],
}

# File extension to language mapping
EXT_LANG_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "javascript",
    ".tsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".rb": "ruby",
    ".go": "go",
}

# Directories to skip
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "vendor", ".tox", ".mypy_cache", ".pytest_cache", "dist",
    "build", ".next", ".nuxt",
}


def parse_env_file(filepath: Path) -> dict[str, str]:
    """Parse a .env-style file, returning var_name -> raw_value mapping."""
    env_vars = {}
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except (OSError, PermissionError):
        return env_vars

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Handle export prefix
        if line.startswith("export "):
            line = line[7:]
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line)
        if match:
            key = match.group(1)
            env_vars[key] = match.group(2).strip().strip("'\"")
    return env_vars


def scan_file(filepath: Path, language: str) -> list[dict[str, Any]]:
    """Scan a single file for env var references."""
    findings = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except (OSError, PermissionError):
        return findings

    patterns = PATTERNS.get(language, [])
    lines = content.splitlines()

    for pattern, pattern_desc in patterns:
        for match in pattern.finditer(content):
            var_name = match.group(1)
            # Find line number
            line_start = content[:match.start()].count("\n")
            line_text = lines[line_start].strip() if line_start < len(lines) else ""
            findings.append({
                "variable": var_name,
                "file": str(filepath),
                "line": line_start + 1,
                "pattern": pattern_desc,
                "language": language,
                "context": line_text,
            })
    return findings


def detect_file_language(filepath: Path) -> str | None:
    """Detect the language/context of a file."""
    name = filepath.name.lower()

    if name == "dockerfile" or name.startswith("dockerfile."):
        return "docker"
    if name == "docker-compose.yml" or name == "docker-compose.yaml" or name.startswith("docker-compose."):
        return "docker_compose"
    if name in (".github",):
        return None
    # GitHub Actions workflows
    parts = filepath.parts
    if ".github" in parts and "workflows" in parts and name.endswith((".yml", ".yaml")):
        return "github_actions"
    if name == ".gitlab-ci.yml":
        return "gitlab_ci"

    ext = filepath.suffix
    return EXT_LANG_MAP.get(ext)


def scan_project(project_dir: str) -> dict[str, Any]:
    """Scan the entire project for env var usage."""
    root = Path(project_dir).resolve()
    if not root.is_dir():
        return {"error": f"Directory not found: {project_dir}"}

    all_references: list[dict[str, Any]] = []
    env_files: dict[str, dict[str, str]] = {}
    scanned_files = 0

    # Walk project tree
    for dirpath, dirnames, filenames in os.walk(root):
        # Filter out skip dirs in-place
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for filename in filenames:
            filepath = Path(dirpath) / filename

            # Parse .env files
            if filename.startswith(".env"):
                rel = str(filepath.relative_to(root))
                env_files[rel] = parse_env_file(filepath)
                continue

            # Detect language and scan
            lang = detect_file_language(filepath)
            if lang:
                refs = scan_file(filepath, lang)
                if refs:
                    # Convert absolute paths to relative
                    for ref in refs:
                        ref["file"] = str(Path(ref["file"]).relative_to(root))
                    all_references.extend(refs)
                scanned_files += 1

    # Aggregate unique variable names
    code_vars = sorted(set(r["variable"] for r in all_references))
    env_defined_vars = set()
    for env_file_vars in env_files.values():
        env_defined_vars.update(env_file_vars.keys())

    # Find gaps
    missing_from_env = sorted(set(code_vars) - env_defined_vars)
    unused_in_code = sorted(env_defined_vars - set(code_vars))

    # Env example analysis
    example_vars = set()
    for fname, fvars in env_files.items():
        if "example" in fname or "sample" in fname or "template" in fname:
            example_vars.update(fvars.keys())

    env_main_vars = set()
    for fname, fvars in env_files.items():
        if fname == ".env":
            env_main_vars.update(fvars.keys())

    missing_from_example = sorted(env_main_vars - example_vars) if example_vars else []

    return {
        "project_dir": str(root),
        "scanned_files": scanned_files,
        "total_references": len(all_references),
        "unique_variables": code_vars,
        "unique_variable_count": len(code_vars),
        "env_files": {k: list(v.keys()) for k, v in env_files.items()},
        "references": all_references,
        "missing_from_env_files": missing_from_env,
        "defined_but_unused": unused_in_code,
        "missing_from_example": missing_from_example,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scan_env.py <project_dir>", file=sys.stderr)
        sys.exit(1)

    project_dir = sys.argv[1]
    result = scan_project(project_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
