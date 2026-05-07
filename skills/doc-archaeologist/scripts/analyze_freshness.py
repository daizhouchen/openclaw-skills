#!/usr/bin/env python3
"""
analyze_freshness.py -- Analyse documentation inventory for staleness and inconsistencies.

Usage:
    python3 analyze_freshness.py <target_dir> <inventory_json>

Outputs JSON findings to stdout.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path


STALE_THRESHOLD_DAYS = 180  # 6 months


def parse_iso(s: str) -> datetime:
    # Handle various ISO formats
    s = s.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return datetime.now(tz=timezone.utc)


def days_ago(iso_str: str) -> int:
    dt = parse_iso(iso_str)
    now = datetime.now(tz=timezone.utc)
    return (now - dt).days


def git_recent_changes(target_dir: str, path: str, days: int = 180) -> int:
    """Count git commits touching a path in the last N days."""
    try:
        since = (datetime.now(tz=timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        result = subprocess.run(
            ["git", "log", "--oneline", f"--since={since}", "--", path],
            capture_output=True, text=True, cwd=target_dir, timeout=10
        )
        if result.returncode == 0:
            return len(result.stdout.strip().splitlines()) if result.stdout.strip() else 0
    except Exception:
        pass
    return -1  # unknown


def check_path_exists(target_dir: str, ref_path: str) -> bool:
    """Check if a referenced file/dir path exists relative to target."""
    # Clean up the reference
    clean = ref_path.strip("`'\"()")
    if clean.startswith("./"):
        clean = clean[2:]

    candidate = Path(target_dir) / clean
    return candidate.exists()


def check_command_exists(cmd_line: str, target_dir: str) -> dict:
    """Check if the first token of a command is a known binary or script."""
    # Extract the base command (first token)
    tokens = cmd_line.strip().split()
    if not tokens:
        return {"exists": True, "command": ""}

    cmd = tokens[0]

    # Skip common shell builtins and operators
    builtins = {
        "cd", "echo", "export", "source", "set", "unset", "alias",
        "if", "then", "else", "fi", "for", "do", "done", "while",
        "case", "esac", "function", "return", "exit", "true", "false",
        "test", "[", "[[", "cat", "ls", "cp", "mv", "rm", "mkdir",
        "chmod", "chown", "grep", "sed", "awk", "find", "sort",
        "head", "tail", "wc", "curl", "wget", "tar", "gzip", "gunzip",
        "sudo", "env", "bash", "sh", "zsh", "python", "python3",
        "ruby", "perl", "node", "java", "javac", "gcc", "g++",
        "docker", "docker-compose", "git",
    }
    if cmd in builtins:
        return {"exists": True, "command": cmd}

    # Check if it's a project-local script
    local_path = Path(target_dir) / cmd
    if local_path.exists():
        return {"exists": True, "command": cmd}

    # Check PATH
    if shutil.which(cmd):
        return {"exists": True, "command": cmd}

    # Check common package manager commands that might be project-specific
    # e.g., npm run X, npx X, yarn X, python -m X, go run X
    pkg_runners = {"npm", "npx", "yarn", "pnpm", "pip", "pipx", "cargo", "go", "make"}
    if cmd in pkg_runners:
        # Check if the runner itself exists
        if shutil.which(cmd):
            return {"exists": True, "command": cmd}
        # Check for Makefile if make
        if cmd == "make" and (Path(target_dir) / "Makefile").exists():
            return {"exists": True, "command": cmd}

    return {"exists": False, "command": cmd}


def analyse(target_dir: str, inventory: dict) -> dict:
    findings = {
        "target_dir": target_dir,
        "analysis_time": datetime.now(tz=timezone.utc).isoformat(),
        "findings": [],
    }

    all_code_env_vars = set()
    for cf in inventory.get("code_files", []):
        all_code_env_vars.update(cf.get("env_vars", []))

    all_doc_env_vars = set()
    for df in inventory.get("doc_files", []):
        all_doc_env_vars.update(df.get("env_vars", []))

    # ---------------------------------------------------------------
    # 1. Staleness check on doc files
    # ---------------------------------------------------------------
    for doc in inventory.get("doc_files", []):
        doc_age = days_ago(doc["last_modified"])
        doc_path = doc["path"]

        if doc_age > STALE_THRESHOLD_DAYS:
            # Check if related code has changed recently
            # Heuristic: check parent dir of the doc
            parent = str(Path(doc_path).parent)
            if parent == ".":
                parent = ""
            code_changes = git_recent_changes(target_dir, parent or ".", 180)

            severity = "warning"
            confidence = 0.5

            if code_changes > 10:
                severity = "critical"
                confidence = 0.85
                detail = (
                    f"Document has not been updated in {doc_age} days, "
                    f"but related code has {code_changes} commits in the last 6 months."
                )
            elif code_changes > 0:
                confidence = 0.65
                detail = (
                    f"Document has not been updated in {doc_age} days, "
                    f"and related code has {code_changes} recent commits."
                )
            elif code_changes == 0:
                severity = "suggestion"
                confidence = 0.3
                detail = (
                    f"Document has not been updated in {doc_age} days. "
                    f"Related code also appears inactive."
                )
            else:
                detail = (
                    f"Document has not been updated in {doc_age} days "
                    f"(git history not available for comparison)."
                )

            findings["findings"].append({
                "type": "stale_document",
                "severity": severity,
                "confidence": confidence,
                "location": doc_path,
                "description": detail,
                "suggested_fix": f"Review and update {doc_path} to reflect current state of the project.",
            })

    # ---------------------------------------------------------------
    # 2. Broken file references
    # ---------------------------------------------------------------
    for doc in inventory.get("doc_files", []):
        for ref in doc.get("file_references", []):
            if not check_path_exists(target_dir, ref):
                # Filter out likely URLs or non-path tokens
                if ref.startswith("http") or ref.startswith("//"):
                    continue
                findings["findings"].append({
                    "type": "broken_reference",
                    "severity": "critical",
                    "confidence": 0.8,
                    "location": f"{doc['path']}",
                    "description": f"References path `{ref}` which does not exist.",
                    "suggested_fix": f"Remove or update the reference to `{ref}` in {doc['path']}.",
                })

    # ---------------------------------------------------------------
    # 3. Invalid commands in code blocks
    # ---------------------------------------------------------------
    for doc in inventory.get("doc_files", []):
        for cmd_line in doc.get("code_block_commands", []):
            result = check_command_exists(cmd_line, target_dir)
            if not result["exists"]:
                findings["findings"].append({
                    "type": "invalid_command",
                    "severity": "warning",
                    "confidence": 0.6,
                    "location": doc["path"],
                    "description": (
                        f"Code block command `{cmd_line[:100]}` references "
                        f"`{result['command']}` which is not found."
                    ),
                    "suggested_fix": (
                        f"Verify the command `{result['command']}` is correct, "
                        f"or add installation instructions."
                    ),
                })

    # ---------------------------------------------------------------
    # 4. Environment variable drift
    # ---------------------------------------------------------------
    # Vars in docs but not in code
    for var in all_doc_env_vars - all_code_env_vars:
        findings["findings"].append({
            "type": "env_var_doc_only",
            "severity": "warning",
            "confidence": 0.5,
            "location": "(documentation)",
            "description": f"Environment variable `{var}` is documented but not found in code.",
            "suggested_fix": f"Verify if `{var}` is still needed; remove from docs if obsolete.",
        })

    # Vars in code but not in docs
    for var in all_code_env_vars - all_doc_env_vars:
        findings["findings"].append({
            "type": "env_var_undocumented",
            "severity": "suggestion",
            "confidence": 0.5,
            "location": "(code)",
            "description": f"Environment variable `{var}` is used in code but not documented.",
            "suggested_fix": f"Add documentation for `{var}` in README or a configuration guide.",
        })

    # ---------------------------------------------------------------
    # 5. TODO/FIXME/DEPRECATED markers
    # ---------------------------------------------------------------
    for cf in inventory.get("code_files", []):
        for marker in cf.get("markers", []):
            if marker["type"] == "DEPRECATED":
                findings["findings"].append({
                    "type": "deprecated_marker",
                    "severity": "warning",
                    "confidence": 0.7,
                    "location": f"{cf['path']}:{marker['line']}",
                    "description": f"DEPRECATED marker: {marker['text'][:150]}",
                    "suggested_fix": "Review whether the deprecated code can be removed.",
                })
            elif marker["type"] in ("FIXME", "BUG"):
                findings["findings"].append({
                    "type": "fixme_marker",
                    "severity": "warning",
                    "confidence": 0.6,
                    "location": f"{cf['path']}:{marker['line']}",
                    "description": f"{marker['type']} marker: {marker['text'][:150]}",
                    "suggested_fix": "Address the issue or create a tracking issue.",
                })

    # Sort: critical first, then warning, then suggestion
    severity_order = {"critical": 0, "warning": 1, "suggestion": 2}
    findings["findings"].sort(key=lambda f: severity_order.get(f["severity"], 9))

    return findings


def main():
    if len(sys.argv) < 3:
        print("Usage: analyze_freshness.py <target_dir> <inventory_json>", file=sys.stderr)
        sys.exit(1)

    target_dir = sys.argv[1]
    inventory_path = sys.argv[2]

    with open(inventory_path, "r") as f:
        inventory = json.load(f)

    results = analyse(target_dir, inventory)
    json.dump(results, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
