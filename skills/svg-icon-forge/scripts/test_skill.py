#!/usr/bin/env python3
"""Test suite for svg-icon-forge skill.

Generates 5 sample icons using templates, optimizes each with optimize_svg.py,
validates they are well-formed XML, and checks file sizes are under 1 KB.
"""

import os
import sys
import xml.etree.ElementTree as ET

# Ensure we can import sibling modules
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from assets.icon_templates import get_icon, STYLES
from scripts.optimize_svg import optimize, validate_svg

# 5 sample icons to test (name, style)
SAMPLES = [
    ("arrow_right", "outline"),
    ("search", "filled"),
    ("edit", "duotone"),
    ("check", "hand-drawn"),
    ("play", "pixel"),
]

OUTPUT_DIR = os.path.join(ROOT, "test_output")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    passed = 0
    failed = 0

    for name, style in SAMPLES:
        label = f"{name} ({style})"
        print(f"\n--- Testing: {label} ---")

        # 1. Generate from template
        svg_raw = get_icon(name, style)
        print(f"  Generated: {len(svg_raw)} bytes")

        # 2. Optimize
        svg_opt = optimize(svg_raw)
        size = len(svg_opt.encode("utf-8"))
        print(f"  Optimized: {size} bytes")

        # 3. Validate XML
        try:
            ET.fromstring(svg_opt)
            print(f"  XML:       VALID")
        except ET.ParseError as e:
            print(f"  XML:       INVALID -- {e}")
            failed += 1
            continue

        # 4. Check size < 1 KB
        if size > 1024:
            print(f"  Size:      FAIL ({size} > 1024)")
            failed += 1
            continue
        else:
            print(f"  Size:      PASS ({size} <= 1024)")

        # 5. Run full validation
        warnings = validate_svg(svg_opt)
        if warnings:
            print(f"  Warnings:")
            for w in warnings:
                print(f"    - {w}")
        else:
            print(f"  Validation: ALL CHECKS PASSED")

        # 6. Save to file
        out_path = os.path.join(OUTPUT_DIR, f"{name}_{style}.svg")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(svg_opt)
        print(f"  Saved:     {out_path}")

        passed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed out of {len(SAMPLES)}")
    print(f"{'='*50}")

    # Additional: test all icons in all styles to make sure none crash
    print(f"\nBulk generation test (all icons x all styles)...")
    from assets.icon_templates import ALL_ICONS
    total = 0
    bulk_errors = 0
    for cat, icons in ALL_ICONS.items():
        for icon_name, fn in icons.items():
            for style in STYLES:
                try:
                    svg = fn(style)
                    ET.fromstring(svg)
                    total += 1
                except Exception as e:
                    print(f"  ERROR: {icon_name}/{style} -- {e}")
                    bulk_errors += 1

    print(f"Bulk test: {total} icons generated and validated, {bulk_errors} errors")

    if failed > 0 or bulk_errors > 0:
        sys.exit(1)
    print("\nAll tests passed!")


if __name__ == "__main__":
    main()
