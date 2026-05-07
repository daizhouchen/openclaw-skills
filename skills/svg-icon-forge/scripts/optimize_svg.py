#!/usr/bin/env python3
"""SVG optimizer and validator for svg-icon-forge.

Usage:
    python optimize_svg.py <input.svg>            # optimize a file
    python optimize_svg.py --string '<svg>...</svg>'  # optimize a string
    python optimize_svg.py --validate <input.svg>     # validate only
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# Attributes considered redundant or editor-specific that can be safely removed
STRIP_ATTRS = {
    "data-name",
    "class",
    "style",
    "xml:space",
    "inkscape:version",
    "sodipodi:docname",
    "inkscape:label",
}

STRIP_ATTR_PREFIXES = ("inkscape:", "sodipodi:", "sketch:", "serif:")

# Namespace URIs to strip (editor namespaces)
STRIP_NS_URIS = {
    "http://www.inkscape.org/namespaces/inkscape",
    "http://sodipodi.sourceforge.net/DTD/sodipodi-0.0.dtd",
    "http://www.bohemiancoding.com/sketch/ns",
    "http://serif.com/",
}


def parse_svg(svg_text: str) -> ET.Element:
    """Parse SVG text into an ElementTree element."""
    # Register the SVG namespace so output stays clean
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    try:
        return ET.fromstring(svg_text)
    except ET.ParseError as e:
        print(f"ERROR: Invalid XML -- {e}", file=sys.stderr)
        sys.exit(1)


def strip_redundant_attrs(element: ET.Element) -> None:
    """Remove editor metadata and redundant attributes recursively."""
    keys_to_remove = []
    for key in element.attrib:
        local = key.split("}")[-1] if "}" in key else key
        if local in STRIP_ATTRS:
            keys_to_remove.append(key)
            continue
        for prefix in STRIP_ATTR_PREFIXES:
            if local.startswith(prefix):
                keys_to_remove.append(key)
                break
    for key in keys_to_remove:
        del element.attrib[key]
    for child in element:
        strip_redundant_attrs(child)


def strip_editor_elements(element: ET.Element) -> None:
    """Remove editor-specific child elements (metadata, namedview, etc.)."""
    removals = []
    for child in element:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag in ("metadata", "namedview", "defs") or any(
            ns in child.tag for ns in STRIP_NS_URIS
        ):
            # Keep <defs> only if it has children
            if tag == "defs" and len(child) > 0:
                continue
            removals.append(child)
    for child in removals:
        element.remove(child)


def ensure_viewbox(root: ET.Element) -> None:
    """Ensure the root <svg> has viewBox='0 0 24 24'."""
    ns = "{http://www.w3.org/2000/svg}"
    tag = root.tag.replace(ns, "")
    if tag != "svg":
        print("ERROR: Root element is not <svg>", file=sys.stderr)
        sys.exit(1)
    root.set("viewBox", "0 0 24 24")
    root.set("width", "24")
    root.set("height", "24")


def simplify_path_data(d: str) -> str:
    """Light simplification of path data -- trim whitespace, collapse spaces."""
    d = re.sub(r"\s+", " ", d.strip())
    # Remove unnecessary spaces around commands
    d = re.sub(r"\s*([MmLlHhVvCcSsQqTtAaZz])\s*", r"\1", d)
    # Add space between number and command for readability where needed
    d = re.sub(r"(\d)([MmLlHhVvCcSsQqTtAaZz])", r"\1 \2", d)
    return d


def optimize_paths(element: ET.Element) -> None:
    """Simplify path data in all <path> elements."""
    ns = "{http://www.w3.org/2000/svg}"
    tag = element.tag.replace(ns, "")
    if tag == "path":
        d = element.get("d", "")
        if d:
            element.set("d", simplify_path_data(d))
    for child in element:
        optimize_paths(child)


def to_string(root: ET.Element) -> str:
    """Serialize the element back to an SVG string."""
    raw = ET.tostring(root, encoding="unicode")
    # Clean up namespace noise that ElementTree adds
    raw = raw.replace(' xmlns:ns0="http://www.w3.org/2000/svg"', "")
    raw = raw.replace("ns0:", "")
    raw = re.sub(r' xmlns=""', "", raw)
    return raw


def validate_svg(svg_text: str) -> list[str]:
    """Validate SVG against icon-forge quality standards. Returns list of warnings."""
    warnings = []
    root = parse_svg(svg_text)
    ns = "{http://www.w3.org/2000/svg}"

    # Check viewBox
    vb = root.get("viewBox", "")
    if vb != "0 0 24 24":
        warnings.append(f"viewBox is '{vb}', expected '0 0 24 24'")

    # Check for currentColor usage
    has_color_ref = "currentColor" in svg_text
    if not has_color_ref:
        warnings.append("No 'currentColor' found -- icon may not adapt to themes")

    # File size
    size = len(svg_text.encode("utf-8"))
    if size > 1024:
        warnings.append(f"File size {size} bytes exceeds 1 KB limit")

    # Check for title element (use 'is not None' -- Element.__bool__ is False when childless)
    title = root.find(f"{ns}title")
    if title is None:
        title = root.find("title")
    if title is None:
        warnings.append("Missing <title> element for accessibility")

    return warnings


def optimize(svg_text: str) -> str:
    """Full optimization pipeline. Returns optimized SVG string."""
    root = parse_svg(svg_text)
    strip_editor_elements(root)
    strip_redundant_attrs(root)
    ensure_viewbox(root)
    optimize_paths(root)
    return to_string(root)


def main():
    parser = argparse.ArgumentParser(description="SVG Icon Optimizer & Validator")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("file", nargs="?", help="Path to SVG file")
    group.add_argument("--string", help="Raw SVG string to optimize")
    parser.add_argument(
        "--validate", action="store_true", help="Validate only, do not optimize"
    )
    parser.add_argument(
        "-o", "--output", help="Output file path (default: stdout)"
    )
    args = parser.parse_args()

    if args.string:
        svg_text = args.string
        source = "<string>"
    else:
        path = Path(args.file)
        if not path.exists():
            print(f"ERROR: File not found: {path}", file=sys.stderr)
            sys.exit(1)
        svg_text = path.read_text(encoding="utf-8")
        source = str(path)

    if args.validate:
        warnings = validate_svg(svg_text)
        if warnings:
            print(f"Validation warnings for {source}:")
            for w in warnings:
                print(f"  - {w}")
            sys.exit(1)
        else:
            size = len(svg_text.encode("utf-8"))
            print(f"PASS: {source} ({size} bytes)")
            sys.exit(0)

    optimized = optimize(svg_text)
    warnings = validate_svg(optimized)

    if args.output:
        Path(args.output).write_text(optimized, encoding="utf-8")
        dest = args.output
    else:
        print(optimized)
        dest = "stdout"

    size = len(optimized.encode("utf-8"))
    print(f"\n--- Optimization Report ---", file=sys.stderr)
    print(f"Source:    {source}", file=sys.stderr)
    print(f"Output:    {dest}", file=sys.stderr)
    print(f"Size:      {size} bytes", file=sys.stderr)
    if warnings:
        print(f"Warnings:", file=sys.stderr)
        for w in warnings:
            print(f"  - {w}", file=sys.stderr)
    else:
        print(f"Status:    ALL CHECKS PASSED", file=sys.stderr)


if __name__ == "__main__":
    main()
