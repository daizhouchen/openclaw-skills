#!/usr/bin/env python3
"""
scan_docs.py -- Scan a project directory for documentation artifacts.

Usage:
    python3 scan_docs.py <target_dir>

Outputs a JSON inventory to stdout.
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DOC_FILE_PATTERNS = [
    "README*",
    "CONTRIBUTING*",
    "CHANGELOG*",
    "LICENSE*",
    "CHANGES*",
    "HISTORY*",
    "AUTHORS*",
    "MIGRATION*",
]

DOC_EXTENSIONS = {".md", ".rst", ".txt", ".adoc", ".textile"}
CODE_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".sh": "shell",
    ".bash": "shell",
}

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__",
    ".tox", ".nox", ".mypy_cache", ".pytest_cache",
    "venv", ".venv", "env", ".env",
    "dist", "build", "target", ".next", ".nuxt",
    "vendor", "bower_components",
}

MARKER_PATTERN = re.compile(
    r"(?:#|//|/\*|\*|--|;)\s*\b(TODO|FIXME|HACK|DEPRECATED|XXX|BUG|NOTE|WARNING)\b[:\s]*(.*)",
    re.IGNORECASE,
)

CODE_BLOCK_RE = re.compile(r"```(?:bash|sh|shell|console|zsh)?\s*\n(.*?)```", re.DOTALL)
FILE_REF_RE = re.compile(r"(?:^|\s|[\(`\[])([./][\w./_-]+(?:\.\w+)?)", re.MULTILINE)
ENV_VAR_MD_RE = re.compile(r"`([A-Z][A-Z0-9_]{2,})`")
ENV_VAR_CODE_RE = re.compile(
    r"""(?:os\.environ(?:\.get)?\s*[\[(]\s*['"]([A-Z][A-Z0-9_]{2,})['"]|"""
    r"""os\.getenv\s*\(\s*['"]([A-Z][A-Z0-9_]{2,})['"]|"""
    r"""os\.environ\s*\[\s*['"]([A-Z][A-Z0-9_]{2,})['"]|"""
    r"""process\.env\.([A-Z][A-Z0-9_]{2,})|"""
    r"""\$\{?([A-Z][A-Z0-9_]{2,})\}?)"""
)

PYTHON_DOCSTRING_RE = re.compile(r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')')
JSDOC_RE = re.compile(r"/\*\*[\s\S]*?\*/")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def file_mtime_iso(path: Path) -> str:
    ts = path.stat().st_mtime
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def is_doc_name(name: str) -> bool:
    upper = name.upper()
    for pat in DOC_FILE_PATTERNS:
        base = pat.rstrip("*")
        if upper.startswith(base.upper()):
            return True
    return False


def extract_sections(text: str):
    """Extract Markdown heading sections."""
    sections = []
    current = None
    for line in text.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            if current:
                sections.append(current)
            current = {"level": len(m.group(1)), "title": m.group(2).strip(), "line_count": 0}
        elif current:
            current["line_count"] += 1
    if current:
        sections.append(current)
    return sections


def extract_code_blocks(text: str):
    """Extract shell commands from fenced code blocks."""
    commands = []
    for m in CODE_BLOCK_RE.finditer(text):
        block = m.group(1).strip()
        for line in block.splitlines():
            line = line.strip()
            if line.startswith("$ "):
                line = line[2:]
            if line and not line.startswith("#"):
                commands.append(line)
    return commands


def extract_file_references(text: str):
    refs = []
    for m in FILE_REF_RE.finditer(text):
        ref = m.group(1)
        if not ref.startswith("//") and len(ref) > 2:
            refs.append(ref)
    return list(set(refs))


def extract_env_vars_from_doc(text: str):
    return list(set(ENV_VAR_MD_RE.findall(text)))


def extract_env_vars_from_code(text: str):
    found = set()
    for m in ENV_VAR_CODE_RE.finditer(text):
        for g in m.groups():
            if g:
                found.add(g)
    return list(found)


def extract_markers(text: str):
    markers = []
    for i, line in enumerate(text.splitlines(), 1):
        m = MARKER_PATTERN.search(line)
        if m:
            markers.append({
                "line": i,
                "type": m.group(1).upper(),
                "text": m.group(2).strip()[:200],
            })
    return markers


def extract_docstrings(text: str, lang: str):
    docs = []
    if lang == "python":
        for m in PYTHON_DOCSTRING_RE.finditer(text):
            content = m.group(0)
            line = text[:m.start()].count("\n") + 1
            docs.append({"line": line, "length": len(content), "preview": content[:120]})
    elif lang in ("javascript", "typescript"):
        for m in JSDOC_RE.finditer(text):
            content = m.group(0)
            line = text[:m.start()].count("\n") + 1
            docs.append({"line": line, "length": len(content), "preview": content[:120]})
    return docs


# ---------------------------------------------------------------------------
# Main scanning logic
# ---------------------------------------------------------------------------

def scan_directory(target_dir: str) -> dict:
    root = Path(target_dir).resolve()
    if not root.is_dir():
        print(f"Error: {target_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    inventory = {
        "target_dir": str(root),
        "scan_time": datetime.now(tz=timezone.utc).isoformat(),
        "doc_files": [],
        "code_files": [],
        "summary": {
            "total_doc_files": 0,
            "total_code_files_with_comments": 0,
            "total_markers": 0,
            "total_docstrings": 0,
        },
    }

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune skip dirs in-place
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        rel_dir = Path(dirpath).relative_to(root)

        for fname in filenames:
            fpath = Path(dirpath) / fname
            if should_skip(fpath.relative_to(root)):
                continue

            ext = fpath.suffix.lower()
            rel_path = str(fpath.relative_to(root))

            # --- Documentation files ---
            is_doc = False
            if ext in DOC_EXTENSIONS:
                is_doc = True
            elif is_doc_name(fname):
                is_doc = True
            elif str(rel_dir).startswith("docs"):
                is_doc = True

            if is_doc and fpath.is_file():
                try:
                    text = fpath.read_text(errors="replace")
                except Exception:
                    continue

                doc_entry = {
                    "path": rel_path,
                    "last_modified": file_mtime_iso(fpath),
                    "size_bytes": fpath.stat().st_size,
                    "line_count": text.count("\n") + 1,
                    "sections": extract_sections(text),
                    "code_block_commands": extract_code_blocks(text),
                    "file_references": extract_file_references(text),
                    "env_vars": extract_env_vars_from_doc(text),
                }
                inventory["doc_files"].append(doc_entry)

            # --- Code files ---
            if ext in CODE_EXTENSIONS and fpath.is_file():
                try:
                    text = fpath.read_text(errors="replace")
                except Exception:
                    continue

                lang = CODE_EXTENSIONS[ext]
                markers = extract_markers(text)
                docstrings = extract_docstrings(text, lang)
                env_vars = extract_env_vars_from_code(text)

                if markers or docstrings or env_vars:
                    code_entry = {
                        "path": rel_path,
                        "language": lang,
                        "last_modified": file_mtime_iso(fpath),
                        "markers": markers,
                        "docstrings": docstrings,
                        "env_vars": env_vars,
                    }
                    inventory["code_files"].append(code_entry)

    # Summary
    inventory["summary"]["total_doc_files"] = len(inventory["doc_files"])
    inventory["summary"]["total_code_files_with_comments"] = len(inventory["code_files"])
    inventory["summary"]["total_markers"] = sum(
        len(cf["markers"]) for cf in inventory["code_files"]
    )
    inventory["summary"]["total_docstrings"] = sum(
        len(cf["docstrings"]) for cf in inventory["code_files"]
    )

    return inventory


def main():
    if len(sys.argv) < 2:
        print("Usage: scan_docs.py <target_dir>", file=sys.stderr)
        sys.exit(1)

    target_dir = sys.argv[1]
    inventory = scan_directory(target_dir)
    json.dump(inventory, sys.stdout, indent=2, ensure_ascii=False)
    print()  # trailing newline


if __name__ == "__main__":
    main()
