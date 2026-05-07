#!/usr/bin/env python3
"""
Codebase Cartographer - Dependency Analyzer

Parses imports across multiple languages, builds a dependency graph,
detects circular dependencies (Tarjan's SCC), and calculates centrality metrics.
Generates an interactive HTML architecture map.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# ---------- Import parsers ----------

# Python: import X / from X import Y
RE_PY_IMPORT = re.compile(
    r'^\s*import\s+([\w.]+)'
    r'|'
    r'^\s*from\s+([\w.]+)\s+import',
    re.MULTILINE,
)

# JavaScript/TypeScript: import ... from '...' / require('...')
RE_JS_IMPORT = re.compile(
    r'''import\s+(?:.*?\s+from\s+)?['"]([^'"]+)['"]'''
    r'''|'''
    r'''require\s*\(\s*['"]([^'"]+)['"]\s*\)''',
    re.MULTILINE,
)

# Go: import "..." or import ( "..." )
RE_GO_IMPORT = re.compile(
    r'''import\s+(?:\(\s*)?["']?([^"'\s\)]+)["']?''',
    re.MULTILINE,
)

# Java: import ...;
RE_JAVA_IMPORT = re.compile(
    r'^\s*import\s+([\w.]+)\s*;',
    re.MULTILINE,
)

PARSERS = {
    "Python": RE_PY_IMPORT,
    "JavaScript": RE_JS_IMPORT,
    "JavaScript (JSX)": RE_JS_IMPORT,
    "TypeScript": RE_JS_IMPORT,
    "TypeScript (TSX)": RE_JS_IMPORT,
    "Go": RE_GO_IMPORT,
    "Java": RE_JAVA_IMPORT,
    "Kotlin": RE_JAVA_IMPORT,
    "Vue": RE_JS_IMPORT,
    "Svelte": RE_JS_IMPORT,
}


def read_file(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


def parse_imports(content: str, language: str):
    """Extract import targets from file content."""
    pattern = PARSERS.get(language)
    if not pattern:
        return []

    imports = []
    for match in pattern.finditer(content):
        groups = match.groups()
        for g in groups:
            if g:
                imports.append(g)
                break
    return imports


def resolve_import(imp: str, source_file: str, root: str, all_files: dict) -> str | None:
    """Try to resolve an import string to a file in the project."""
    source_dir = os.path.dirname(source_file)
    lang = all_files.get(source_file, {}).get("language", "")

    if lang in ("Python",):
        # Convert dotted path to file path
        parts = imp.replace(".", "/")
        candidates = [
            parts + ".py",
            parts + "/__init__.py",
            os.path.join(source_dir, parts + ".py"),
            os.path.join(source_dir, parts + "/__init__.py"),
        ]
        for c in candidates:
            normed = os.path.normpath(c)
            if normed in all_files:
                return normed
    elif lang in ("JavaScript", "JavaScript (JSX)", "TypeScript", "TypeScript (TSX)", "Vue", "Svelte"):
        # Relative imports
        if imp.startswith("."):
            base = os.path.normpath(os.path.join(source_dir, imp))
            exts = [".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", "/index.js",
                    "/index.ts", "/index.jsx", "/index.tsx"]
            # Try exact match first
            if base in all_files:
                return base
            for ext in exts:
                candidate = base + ext
                normed = os.path.normpath(candidate)
                if normed in all_files:
                    return normed
        else:
            # Non-relative = likely external package, skip
            return None
    elif lang == "Go":
        # Try to match by last path segment
        parts = imp.split("/")
        for fpath in all_files:
            if fpath.endswith(".go") and parts[-1] in fpath:
                return fpath
        return None
    elif lang in ("Java", "Kotlin"):
        # Convert package path to file
        parts = imp.replace(".", "/")
        candidates = [parts + ".java", parts + ".kt"]
        for c in candidates:
            if c in all_files:
                return c
        return None

    return None


# ---------- Tarjan's SCC ----------

def tarjan_scc(graph: dict):
    """Find all strongly connected components using Tarjan's algorithm."""
    index_counter = [0]
    stack = []
    lowlink = {}
    index = {}
    on_stack = {}
    result = []

    def strongconnect(v):
        index[v] = index_counter[0]
        lowlink[v] = index_counter[0]
        index_counter[0] += 1
        stack.append(v)
        on_stack[v] = True

        for w in graph.get(v, []):
            if w not in index:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif on_stack.get(w, False):
                lowlink[v] = min(lowlink[v], index[w])

        if lowlink[v] == index[v]:
            component = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                component.append(w)
                if w == v:
                    break
            result.append(component)

    for v in graph:
        if v not in index:
            strongconnect(v)

    return result


# ---------- Main analysis ----------

def analyze(scan_data: dict):
    root = scan_data["root"]
    files_info = {f["path"]: f for f in scan_data["files"]}

    # Build adjacency list
    adjacency = defaultdict(list)  # source -> [targets]
    reverse_adj = defaultdict(list)  # target -> [sources]
    all_nodes = set()

    for finfo in scan_data["files"]:
        fpath = finfo["path"]
        lang = finfo["language"]

        if lang not in PARSERS:
            continue

        all_nodes.add(fpath)
        full_path = os.path.join(root, fpath)
        content = read_file(full_path)
        imports = parse_imports(content, lang)

        for imp in imports:
            resolved = resolve_import(imp, fpath, root, files_info)
            if resolved and resolved != fpath:
                all_nodes.add(resolved)
                if resolved not in adjacency[fpath]:
                    adjacency[fpath].append(resolved)
                if fpath not in reverse_adj[resolved]:
                    reverse_adj[resolved].append(fpath)

    # Ensure all nodes with parseable languages are included
    for finfo in scan_data["files"]:
        if finfo["language"] in PARSERS:
            all_nodes.add(finfo["path"])

    # Build full graph dict for Tarjan
    full_graph = {node: adjacency.get(node, []) for node in all_nodes}

    # Find SCCs (circular dependencies)
    sccs = tarjan_scc(full_graph)
    circular = [scc for scc in sccs if len(scc) > 1]

    # Flatten circular nodes for quick lookup
    circular_nodes = set()
    for scc in circular:
        for node in scc:
            circular_nodes.add(node)

    # Calculate degrees
    node_metrics = {}
    for node in all_nodes:
        out_deg = len(adjacency.get(node, []))
        in_deg = len(reverse_adj.get(node, []))
        node_metrics[node] = {
            "in_degree": in_deg,
            "out_degree": out_deg,
            "total_degree": in_deg + out_deg,
            "is_circular": node in circular_nodes,
        }

    # Classify nodes
    hubs = []        # high in-degree
    orchestrators = []  # high out-degree
    islands = []     # zero connections

    if node_metrics:
        degrees = [m["total_degree"] for m in node_metrics.values()]
        avg_degree = sum(degrees) / len(degrees) if degrees else 0
        threshold = max(avg_degree * 1.5, 2)

        for node, m in node_metrics.items():
            if m["total_degree"] == 0:
                islands.append(node)
            elif m["in_degree"] >= threshold:
                hubs.append(node)
            elif m["out_degree"] >= threshold:
                orchestrators.append(node)

    # Build edges list for visualization
    edges = []
    for source, targets in adjacency.items():
        for target in targets:
            is_circ = (source in circular_nodes and target in circular_nodes)
            edges.append({
                "source": source,
                "target": target,
                "circular": is_circ,
            })

    # Build nodes list
    nodes = []
    for node in all_nodes:
        finfo = files_info.get(node, {})
        m = node_metrics.get(node, {"in_degree": 0, "out_degree": 0,
                                     "total_degree": 0, "is_circular": False})
        directory = os.path.dirname(node) or "(root)"
        nodes.append({
            "id": node,
            "language": finfo.get("language", "Unknown"),
            "lines": finfo.get("lines", 0),
            "size": finfo.get("size", 0),
            "directory": directory,
            "in_degree": m["in_degree"],
            "out_degree": m["out_degree"],
            "total_degree": m["total_degree"],
            "is_circular": m["is_circular"],
        })

    result = {
        "root": root,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "circular_dependencies": circular,
        "hubs": sorted(hubs),
        "orchestrators": sorted(orchestrators),
        "islands": sorted(islands),
        "nodes": nodes,
        "edges": edges,
    }
    return result


def generate_html(deps_data: dict, template_path: str, output_path: str):
    """Inject dependency data into the HTML template and write the map."""
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError:
        print(f"Warning: Template not found at {template_path}, generating inline.", file=sys.stderr)
        template = get_fallback_template()

    data_json = json.dumps(deps_data, ensure_ascii=False)
    html = template.replace("/*__GRAPH_DATA__*/", f"const GRAPH_DATA = {data_json};")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Interactive map written to: {output_path}")


def get_fallback_template():
    """Minimal fallback if template file is missing."""
    return """<!DOCTYPE html>
<html><head><title>Codebase Map</title></head>
<body><script>/*__GRAPH_DATA__*/</script>
<pre id="out"></pre>
<script>document.getElementById('out').textContent = JSON.stringify(GRAPH_DATA, null, 2);</script>
</body></html>"""


def main():
    parser = argparse.ArgumentParser(description="Analyze dependencies and generate map")
    parser.add_argument("--scan", "-s", default="carto_scan.json",
                        help="Path to scan JSON from scan.py")
    parser.add_argument("--output", "-o", default="carto_deps.json",
                        help="Output dependency JSON file")
    parser.add_argument("--html", default="carto_map.html",
                        help="Output HTML map file")
    parser.add_argument("--template", default=None,
                        help="Path to HTML template (default: auto-detect)")
    args = parser.parse_args()

    if not os.path.isfile(args.scan):
        print(f"Error: scan file not found: {args.scan}", file=sys.stderr)
        print("Run scan.py first to generate the scan output.", file=sys.stderr)
        sys.exit(1)

    with open(args.scan, "r", encoding="utf-8") as f:
        scan_data = json.load(f)

    print(f"Analyzing dependencies for {scan_data['root']}...")
    deps = analyze(scan_data)

    # Write deps JSON
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(deps, f, indent=2, ensure_ascii=False)

    print(f"Dependency graph: {deps['total_nodes']} nodes, {deps['total_edges']} edges")
    if deps["circular_dependencies"]:
        print(f"Circular dependencies found: {len(deps['circular_dependencies'])} cycle(s)")
        for i, scc in enumerate(deps["circular_dependencies"], 1):
            print(f"  Cycle {i}: {' -> '.join(scc)}")
    if deps["hubs"]:
        print(f"Hub modules (high in-degree): {', '.join(deps['hubs'])}")
    if deps["orchestrators"]:
        print(f"Orchestrators (high out-degree): {', '.join(deps['orchestrators'])}")
    if deps["islands"]:
        print(f"Island modules (no connections): {len(deps['islands'])}")

    print(f"Deps JSON written to: {args.output}")

    # Generate HTML map
    if args.template:
        template_path = args.template
    else:
        # Auto-detect: look relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(script_dir, "..", "assets", "map_template.html")

    generate_html(deps, template_path, args.html)


if __name__ == "__main__":
    main()
