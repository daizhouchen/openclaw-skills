#!/usr/bin/env python3
"""
Codebase Cartographer - Repository Scanner

Recursively scans a directory, classifies files by language/type,
detects project type, package manager, and framework.
Outputs JSON with file list, metadata, and statistics.
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

# ---------- configuration ----------

DEFAULT_EXCLUDES = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", ".nuxt", ".svelte-kit", "target",
    ".idea", ".vscode", ".eggs", "*.egg-info", ".tox", ".mypy_cache",
    ".pytest_cache", ".gradle", ".DS_Store", "vendor", "coverage",
    ".cache", ".parcel-cache",
}

LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript (JSX)",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (TSX)",
    ".go": "Go",
    ".java": "Java",
    ".kt": "Kotlin",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".c": "C",
    ".h": "C/C++ Header",
    ".cpp": "C++",
    ".cc": "C++",
    ".cs": "C#",
    ".swift": "Swift",
    ".m": "Objective-C",
    ".scala": "Scala",
    ".lua": "Lua",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".r": "R",
    ".R": "R",
    ".dart": "Dart",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".hs": "Haskell",
    ".ml": "OCaml",
    ".clj": "Clojure",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "SASS",
    ".less": "LESS",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".xml": "XML",
    ".md": "Markdown",
    ".rst": "reStructuredText",
    ".sql": "SQL",
    ".graphql": "GraphQL",
    ".gql": "GraphQL",
    ".proto": "Protocol Buffers",
    ".tf": "Terraform",
    ".dockerfile": "Dockerfile",
}

# Markers that hint at project type
FRONTEND_MARKERS = {
    "package.json", "tsconfig.json", "next.config.js", "next.config.mjs",
    "nuxt.config.js", "nuxt.config.ts", "vite.config.js", "vite.config.ts",
    "angular.json", "svelte.config.js", "webpack.config.js",
}
BACKEND_MARKERS = {
    "requirements.txt", "setup.py", "pyproject.toml", "Pipfile",
    "go.mod", "Cargo.toml", "pom.xml", "build.gradle",
    "Gemfile", "composer.json", "mix.exs",
}
FRAMEWORK_FILES = {
    "next.config.js": "Next.js", "next.config.mjs": "Next.js",
    "nuxt.config.js": "Nuxt", "nuxt.config.ts": "Nuxt",
    "angular.json": "Angular",
    "svelte.config.js": "SvelteKit",
    "vite.config.js": "Vite", "vite.config.ts": "Vite",
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI",
    "go.mod": "Go Modules",
    "Cargo.toml": "Cargo (Rust)",
    "pom.xml": "Maven", "build.gradle": "Gradle",
    "mix.exs": "Mix (Elixir)",
}
PKG_MANAGER_FILES = {
    "package-lock.json": "npm",
    "yarn.lock": "yarn",
    "pnpm-lock.yaml": "pnpm",
    "bun.lockb": "bun",
    "requirements.txt": "pip",
    "Pipfile.lock": "pipenv",
    "poetry.lock": "poetry",
    "pdm.lock": "pdm",
    "go.sum": "go modules",
    "Cargo.lock": "cargo",
    "Gemfile.lock": "bundler",
    "composer.lock": "composer",
}


def should_exclude(name: str, extra_excludes: set) -> bool:
    all_excludes = DEFAULT_EXCLUDES | extra_excludes
    return name in all_excludes


def count_lines(filepath: str) -> int:
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def classify_language(ext: str, filename: str) -> str:
    lower = filename.lower()
    if lower == "dockerfile" or lower.startswith("dockerfile."):
        return "Dockerfile"
    if lower == "makefile":
        return "Makefile"
    return LANGUAGE_MAP.get(ext.lower(), "Other")


def scan_directory(root: str, extra_excludes: set):
    root = os.path.abspath(root)
    files = []
    root_files = set()
    lang_stats = defaultdict(lambda: {"count": 0, "lines": 0, "bytes": 0})
    total_lines = 0
    total_bytes = 0

    for dirpath, dirnames, filenames in os.walk(root):
        # Filter excluded dirs in-place
        dirnames[:] = [
            d for d in dirnames if not should_exclude(d, extra_excludes)
        ]

        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir == ".":
            rel_dir = ""

        for fname in filenames:
            full = os.path.join(dirpath, fname)
            rel = os.path.join(rel_dir, fname) if rel_dir else fname

            # Track root-level files for detection
            if rel_dir == "":
                root_files.add(fname)

            try:
                size = os.path.getsize(full)
            except OSError:
                size = 0

            ext = os.path.splitext(fname)[1]
            lang = classify_language(ext, fname)
            lines = count_lines(full) if lang != "Other" else 0

            files.append({
                "path": rel,
                "language": lang,
                "extension": ext,
                "size": size,
                "lines": lines,
            })

            lang_stats[lang]["count"] += 1
            lang_stats[lang]["lines"] += lines
            lang_stats[lang]["bytes"] += size
            total_lines += lines
            total_bytes += size

    # Detect project type
    has_frontend = bool(root_files & FRONTEND_MARKERS)
    has_backend = bool(root_files & BACKEND_MARKERS)
    if has_frontend and has_backend:
        project_type = "fullstack"
    elif has_frontend:
        project_type = "frontend"
    elif has_backend:
        project_type = "backend"
    else:
        # Heuristic: check dominant language
        code_langs = {
            k: v for k, v in lang_stats.items()
            if k not in ("Other", "JSON", "YAML", "TOML", "XML", "Markdown",
                         "reStructuredText", "HTML", "CSS", "SCSS", "SASS", "LESS")
        }
        if code_langs:
            dominant = max(code_langs, key=lambda k: code_langs[k]["lines"])
            if dominant in ("JavaScript", "JavaScript (JSX)", "TypeScript",
                            "TypeScript (TSX)", "Vue", "Svelte"):
                project_type = "frontend"
            else:
                project_type = "library"
        else:
            project_type = "unknown"

    # Detect framework
    frameworks = []
    for fname, fw in FRAMEWORK_FILES.items():
        if fname in root_files:
            frameworks.append(fw)
    # Check Python frameworks via imports (basic check in requirements/pyproject)
    for marker in ("requirements.txt", "pyproject.toml", "setup.py", "Pipfile"):
        marker_path = os.path.join(root, marker)
        if os.path.isfile(marker_path):
            try:
                with open(marker_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read().lower()
                for fw_key, fw_name in [("django", "Django"), ("flask", "Flask"),
                                         ("fastapi", "FastAPI"), ("starlette", "Starlette"),
                                         ("tornado", "Tornado"), ("express", "Express")]:
                    if fw_key in content and fw_name not in frameworks:
                        frameworks.append(fw_name)
            except Exception:
                pass

    # Detect package manager
    pkg_managers = []
    for fname, pm in PKG_MANAGER_FILES.items():
        if fname in root_files:
            pkg_managers.append(pm)

    result = {
        "root": root,
        "total_files": len(files),
        "total_lines": total_lines,
        "total_bytes": total_bytes,
        "project_type": project_type,
        "frameworks": frameworks,
        "package_managers": pkg_managers,
        "language_stats": dict(lang_stats),
        "files": files,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description="Scan a code repository")
    parser.add_argument("directory", help="Root directory to scan")
    parser.add_argument("--output", "-o", default="carto_scan.json",
                        help="Output JSON file path")
    parser.add_argument("--exclude", "-e", default="",
                        help="Comma-separated additional directories to exclude")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a directory", file=sys.stderr)
        sys.exit(1)

    extra = set(x.strip() for x in args.exclude.split(",") if x.strip())
    result = scan_directory(args.directory, extra)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Scanned {result['total_files']} files in {result['root']}")
    print(f"Project type: {result['project_type']}")
    if result["frameworks"]:
        print(f"Frameworks: {', '.join(result['frameworks'])}")
    if result["package_managers"]:
        print(f"Package managers: {', '.join(result['package_managers'])}")
    print(f"Languages found: {len(result['language_stats'])}")
    # Top 5 languages by lines
    top = sorted(result["language_stats"].items(),
                 key=lambda x: x[1]["lines"], reverse=True)[:5]
    for lang, stats in top:
        print(f"  {lang}: {stats['count']} files, {stats['lines']} lines")
    print(f"Output written to: {args.output}")


if __name__ == "__main__":
    main()
