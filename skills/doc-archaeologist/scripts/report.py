#!/usr/bin/env python3
"""
report.py -- Generate a documentation archaeology report from analysis findings.

Usage:
    python3 report.py <target_dir> <findings_json>

Creates:
    <target_dir>/doc-archaeology-report.md
    <target_dir>/fix-suggestions/  (diff patches for fixable issues)
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def compute_grade(findings: list) -> str:
    """Compute an A-F health grade based on findings."""
    critical = sum(1 for f in findings if f["severity"] == "critical")
    warnings = sum(1 for f in findings if f["severity"] == "warning")
    suggestions = sum(1 for f in findings if f["severity"] == "suggestion")

    # Simple scoring: each critical = -20, warning = -5, suggestion = -1
    score = 100 - (critical * 20) - (warnings * 5) - (suggestions * 1)
    score = max(0, min(100, score))

    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def grade_description(grade: str) -> str:
    return {
        "A": "Excellent -- documentation is well-maintained and consistent.",
        "B": "Good -- minor issues detected, mostly suggestions.",
        "C": "Fair -- several inconsistencies or stale documents found.",
        "D": "Poor -- significant documentation problems need attention.",
        "F": "Critical -- documentation is severely outdated or broken.",
    }.get(grade, "Unknown")


def severity_icon(severity: str) -> str:
    return {
        "critical": "[CRITICAL]",
        "warning": "[WARNING]",
        "suggestion": "[SUGGESTION]",
    }.get(severity, "[INFO]")


def generate_report(target_dir: str, analysis: dict) -> str:
    findings = analysis.get("findings", [])
    grade = compute_grade(findings)
    analysis_time = analysis.get("analysis_time", datetime.now(tz=timezone.utc).isoformat())

    critical_findings = [f for f in findings if f["severity"] == "critical"]
    warning_findings = [f for f in findings if f["severity"] == "warning"]
    suggestion_findings = [f for f in findings if f["severity"] == "suggestion"]

    lines = []
    lines.append("# Documentation Archaeology Report")
    lines.append("")
    lines.append(f"**Target**: `{target_dir}`")
    lines.append(f"**Generated**: {analysis_time}")
    lines.append("")

    # -- Health Score --
    lines.append("## Document Health Score")
    lines.append("")
    lines.append(f"**Grade: {grade}** -- {grade_description(grade)}")
    lines.append("")
    lines.append(f"| Metric | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Critical issues | {len(critical_findings)} |")
    lines.append(f"| Warnings | {len(warning_findings)} |")
    lines.append(f"| Suggestions | {len(suggestion_findings)} |")
    lines.append(f"| Total findings | {len(findings)} |")
    lines.append("")

    # -- Critical Findings --
    if critical_findings:
        lines.append("## Critical Findings")
        lines.append("")
        for i, f in enumerate(critical_findings, 1):
            lines.append(f"### {i}. {f['type'].replace('_', ' ').title()}")
            lines.append("")
            lines.append(f"- **Location**: `{f['location']}`")
            lines.append(f"- **Problem**: {f['description']}")
            lines.append(f"- **Suggested fix**: {f['suggested_fix']}")
            lines.append(f"- **Confidence**: {f['confidence']:.0%}")
            lines.append("")
    else:
        lines.append("## Critical Findings")
        lines.append("")
        lines.append("No critical findings -- great!")
        lines.append("")

    # -- Warnings --
    if warning_findings:
        lines.append("## Warnings")
        lines.append("")
        for i, f in enumerate(warning_findings, 1):
            lines.append(f"### {i}. {f['type'].replace('_', ' ').title()}")
            lines.append("")
            lines.append(f"- **Location**: `{f['location']}`")
            lines.append(f"- **Problem**: {f['description']}")
            lines.append(f"- **Suggested fix**: {f['suggested_fix']}")
            lines.append(f"- **Confidence**: {f['confidence']:.0%}")
            lines.append("")
    else:
        lines.append("## Warnings")
        lines.append("")
        lines.append("No warnings detected.")
        lines.append("")

    # -- Suggestions --
    if suggestion_findings:
        lines.append("## Suggestions")
        lines.append("")
        for i, f in enumerate(suggestion_findings, 1):
            lines.append(f"### {i}. {f['type'].replace('_', ' ').title()}")
            lines.append("")
            lines.append(f"- **Location**: `{f['location']}`")
            lines.append(f"- **Problem**: {f['description']}")
            lines.append(f"- **Suggested fix**: {f['suggested_fix']}")
            lines.append(f"- **Confidence**: {f['confidence']:.0%}")
            lines.append("")
    else:
        lines.append("## Suggestions")
        lines.append("")
        lines.append("No additional suggestions.")
        lines.append("")

    # -- Full Finding Table --
    if findings:
        lines.append("## All Findings Detail")
        lines.append("")
        lines.append("| # | Severity | Type | Location | Confidence |")
        lines.append("|---|----------|------|----------|------------|")
        for i, f in enumerate(findings, 1):
            sev = severity_icon(f["severity"])
            ftype = f["type"].replace("_", " ").title()
            loc = f["location"][:50]
            conf = f"{f['confidence']:.0%}"
            lines.append(f"| {i} | {sev} | {ftype} | `{loc}` | {conf} |")
        lines.append("")

    return "\n".join(lines)


def generate_fix_patches(target_dir: str, findings: list):
    """Create simple fix-suggestion files for fixable issues."""
    fix_dir = Path(target_dir) / "fix-suggestions"
    fix_dir.mkdir(exist_ok=True)

    patch_count = 0
    for i, f in enumerate(findings):
        if f["type"] == "broken_reference":
            patch_count += 1
            patch_path = fix_dir / f"fix-{patch_count:03d}-broken-ref.md"
            patch_path.write_text(
                f"# Fix: Broken Reference\n\n"
                f"**File**: `{f['location']}`\n"
                f"**Problem**: {f['description']}\n\n"
                f"## Suggested Action\n\n"
                f"{f['suggested_fix']}\n"
            )
        elif f["type"] == "stale_document" and f["severity"] == "critical":
            patch_count += 1
            patch_path = fix_dir / f"fix-{patch_count:03d}-stale-doc.md"
            patch_path.write_text(
                f"# Fix: Stale Document\n\n"
                f"**File**: `{f['location']}`\n"
                f"**Problem**: {f['description']}\n\n"
                f"## Suggested Action\n\n"
                f"{f['suggested_fix']}\n"
            )
        elif f["type"] == "invalid_command":
            patch_count += 1
            patch_path = fix_dir / f"fix-{patch_count:03d}-invalid-cmd.md"
            patch_path.write_text(
                f"# Fix: Invalid Command\n\n"
                f"**File**: `{f['location']}`\n"
                f"**Problem**: {f['description']}\n\n"
                f"## Suggested Action\n\n"
                f"{f['suggested_fix']}\n"
            )

    # Write a summary if we created any patches
    if patch_count > 0:
        summary = fix_dir / "README.md"
        summary.write_text(
            f"# Fix Suggestions\n\n"
            f"This directory contains {patch_count} fix suggestion(s) "
            f"generated by the doc-archaeologist.\n\n"
            f"Review each file and apply the suggested changes.\n"
        )

    return patch_count


def main():
    if len(sys.argv) < 3:
        print("Usage: report.py <target_dir> <findings_json>", file=sys.stderr)
        sys.exit(1)

    target_dir = sys.argv[1]
    findings_path = sys.argv[2]

    with open(findings_path, "r") as f:
        analysis = json.load(f)

    # Generate report
    report_text = generate_report(target_dir, analysis)
    report_path = Path(target_dir) / "doc-archaeology-report.md"
    report_path.write_text(report_text)
    print(f"Report written to: {report_path}", file=sys.stderr)

    # Generate fix suggestions
    patch_count = generate_fix_patches(target_dir, analysis.get("findings", []))
    if patch_count:
        print(f"Generated {patch_count} fix suggestion(s) in fix-suggestions/", file=sys.stderr)
    else:
        print("No auto-fixable issues found.", file=sys.stderr)


if __name__ == "__main__":
    main()
