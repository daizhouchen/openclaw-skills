#!/usr/bin/env python3
"""
Data Detective -- Investigation Script
Analyzes CSV/JSON data files and outputs structured findings as JSON.
"""

import sys
import json
import os
import warnings
from pathlib import Path

import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

OUTPUT_PATH = "/tmp/data_detective_findings.json"


def load_data(filepath: str) -> pd.DataFrame:
    """Load data from CSV, JSON, or Excel."""
    ext = Path(filepath).suffix.lower()
    if ext == ".csv":
        # Try common encodings
        for enc in ("utf-8", "latin-1", "cp1252", "gbk"):
            try:
                return pd.read_csv(filepath, encoding=enc)
            except (UnicodeDecodeError, UnicodeError):
                continue
        raise ValueError(f"Could not decode CSV with common encodings: {filepath}")
    elif ext == ".json":
        return pd.read_json(filepath)
    elif ext in (".xlsx", ".xls"):
        return pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


# ---------------------------------------------------------------------------
# Phase 1: Scene Survey
# ---------------------------------------------------------------------------
def scene_survey(df: pd.DataFrame) -> dict:
    """Basic shape, dtypes, missing values, and descriptive stats."""
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)

    stats = {}
    for col in df.select_dtypes(include="number").columns:
        s = df[col].describe().to_dict()
        stats[col] = {k: round(float(v), 4) if isinstance(v, (float, np.floating)) else int(v)
                       for k, v in s.items()}

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_values": {col: int(v) for col, v in missing.items() if v > 0},
        "missing_pct": {col: float(v) for col, v in missing_pct.items() if v > 0},
        "numeric_stats": stats,
    }


# ---------------------------------------------------------------------------
# Phase 2: Fingerprinting
# ---------------------------------------------------------------------------
def fingerprinting(df: pd.DataFrame) -> dict:
    """Duplicate detection, format consistency, encoding issues."""
    # Duplicates
    dup_count = int(df.duplicated().sum())
    dup_indices = df[df.duplicated()].index.tolist()[:20]  # first 20

    # Format consistency checks per string column
    format_issues = {}
    for col in df.select_dtypes(include="object").columns:
        series = df[col].dropna().astype(str)
        if len(series) == 0:
            continue
        issues = []

        # Check for leading/trailing whitespace
        ws = (series != series.str.strip()).sum()
        if ws > 0:
            issues.append(f"{int(ws)} values have leading/trailing whitespace")

        # Check for mixed case patterns (e.g. "New York" vs "new york")
        lower = series.str.lower()
        unique_raw = series.nunique()
        unique_lower = lower.nunique()
        if unique_lower < unique_raw:
            issues.append(f"{unique_raw - unique_lower} case-inconsistent variants detected")

        # Check for date-like columns with mixed formats
        if any(kw in col.lower() for kw in ("date", "time", "dt", "day")):
            # Try to detect mixed date formats
            sample = series.head(100)
            has_slash = sample.str.contains(r"\d{1,4}/\d{1,2}/\d{1,4}").any()
            has_dash = sample.str.contains(r"\d{1,4}-\d{1,2}-\d{1,4}").any()
            if has_slash and has_dash:
                issues.append("Mixed date separators (/ and -) detected")

        if issues:
            format_issues[col] = issues

    return {
        "duplicate_rows": dup_count,
        "duplicate_indices": dup_indices,
        "format_issues": format_issues,
    }


# ---------------------------------------------------------------------------
# Phase 3: Anomaly Tracking
# ---------------------------------------------------------------------------
def anomaly_tracking(df: pd.DataFrame) -> dict:
    """IQR + Z-score outliers for numeric cols; rare categories."""
    outliers = {}
    numeric_cols = df.select_dtypes(include="number").columns

    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 10:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1

        iqr_lower = q1 - 1.5 * iqr
        iqr_upper = q3 + 1.5 * iqr
        iqr_outliers = series[(series < iqr_lower) | (series > iqr_upper)]

        mean = series.mean()
        std = series.std()
        if std > 0:
            z_scores = ((series - mean) / std).abs()
            z_outliers = series[z_scores > 3]
        else:
            z_outliers = pd.Series(dtype=float)

        if len(iqr_outliers) > 0 or len(z_outliers) > 0:
            outliers[col] = {
                "iqr_outlier_count": int(len(iqr_outliers)),
                "iqr_bounds": [round(float(iqr_lower), 4), round(float(iqr_upper), 4)],
                "iqr_outlier_values": sorted(iqr_outliers.tolist())[:10],
                "zscore_outlier_count": int(len(z_outliers)),
                "zscore_outlier_values": sorted(z_outliers.tolist())[:10],
            }

    # Rare categories
    rare_categories = {}
    for col in df.select_dtypes(include="object").columns:
        vc = df[col].value_counts(normalize=True)
        rare = vc[vc < 0.02]  # less than 2%
        if len(rare) > 0 and len(vc) > 2:
            rare_categories[col] = {
                "rare_values": rare.index.tolist()[:10],
                "rare_pcts": [round(float(v * 100), 2) for v in rare.values[:10]],
                "total_unique": int(len(vc)),
            }

    return {
        "numeric_outliers": outliers,
        "rare_categories": rare_categories,
    }


# ---------------------------------------------------------------------------
# Phase 4: Correlation Search
# ---------------------------------------------------------------------------
def correlation_search(df: pd.DataFrame) -> dict:
    """Numeric correlations, category-numeric group diffs, distribution shapes."""
    numeric_cols = df.select_dtypes(include="number").columns
    cat_cols = df.select_dtypes(include="object").columns

    # Correlation matrix
    strong_correlations = []
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr()
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                r = corr.iloc[i, j]
                if abs(r) > 0.5 and not np.isnan(r):
                    strong_correlations.append({
                        "col_a": numeric_cols[i],
                        "col_b": numeric_cols[j],
                        "correlation": round(float(r), 4),
                        "strength": "strong" if abs(r) > 0.7 else "moderate",
                    })
    strong_correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)

    # Category-numeric group differences
    group_differences = []
    for cat in cat_cols:
        nunique = df[cat].nunique()
        if 2 <= nunique <= 20:
            for num in numeric_cols:
                groups = df.groupby(cat)[num].mean()
                if len(groups) < 2:
                    continue
                overall_mean = df[num].mean()
                if overall_mean == 0:
                    continue
                max_diff = float((groups - overall_mean).abs().max())
                pct_diff = round(max_diff / abs(overall_mean) * 100, 2)
                if pct_diff > 15:
                    group_differences.append({
                        "category_col": cat,
                        "numeric_col": num,
                        "max_pct_diff_from_mean": pct_diff,
                        "group_means": {str(k): round(float(v), 4) for k, v in groups.items()},
                    })
    group_differences.sort(key=lambda x: x["max_pct_diff_from_mean"], reverse=True)

    # Distribution shapes (skewness)
    distribution_info = {}
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 10:
            continue
        skew = float(series.skew())
        kurt = float(series.kurtosis())
        distribution_info[col] = {
            "skewness": round(skew, 4),
            "kurtosis": round(kurt, 4),
            "shape": ("right-skewed" if skew > 1 else
                      "left-skewed" if skew < -1 else
                      "roughly symmetric"),
        }

    return {
        "strong_correlations": strong_correlations[:10],
        "group_differences": group_differences[:10],
        "distributions": distribution_info,
    }


# ---------------------------------------------------------------------------
# Phase 5: Summary
# ---------------------------------------------------------------------------
def build_summary(scene: dict, fingerprint: dict, anomalies: dict, correlations: dict) -> dict:
    """Top 3 findings with severity and confidence."""
    findings = []

    # Missing data
    if scene["missing_values"]:
        worst_col = max(scene["missing_pct"], key=scene["missing_pct"].get)
        worst_pct = scene["missing_pct"][worst_col]
        severity = "critical" if worst_pct > 20 else "warning" if worst_pct > 5 else "info"
        findings.append({
            "title": f"Missing data detected ({len(scene['missing_values'])} columns affected)",
            "detail": f"Worst: '{worst_col}' has {worst_pct}% missing values.",
            "severity": severity,
            "confidence": 1.0,
        })

    # Duplicates
    if fingerprint["duplicate_rows"] > 0:
        dup_pct = round(fingerprint["duplicate_rows"] / scene["rows"] * 100, 2)
        severity = "critical" if dup_pct > 5 else "warning"
        findings.append({
            "title": f"{fingerprint['duplicate_rows']} duplicate rows ({dup_pct}%)",
            "detail": f"Found {fingerprint['duplicate_rows']} exact duplicate rows in the dataset.",
            "severity": severity,
            "confidence": 1.0,
        })

    # Format issues
    if fingerprint["format_issues"]:
        issues_flat = []
        for col, issues in fingerprint["format_issues"].items():
            for iss in issues:
                issues_flat.append(f"{col}: {iss}")
        findings.append({
            "title": f"Format inconsistencies in {len(fingerprint['format_issues'])} column(s)",
            "detail": "; ".join(issues_flat[:5]),
            "severity": "warning",
            "confidence": 0.9,
        })

    # Outliers
    total_outlier_cols = len(anomalies["numeric_outliers"])
    if total_outlier_cols > 0:
        total_iqr = sum(v["iqr_outlier_count"] for v in anomalies["numeric_outliers"].values())
        findings.append({
            "title": f"Outliers detected in {total_outlier_cols} numeric column(s)",
            "detail": f"{total_iqr} total IQR-based outlier values across affected columns.",
            "severity": "warning",
            "confidence": 0.85,
        })

    # Strong correlations
    if correlations["strong_correlations"]:
        top = correlations["strong_correlations"][0]
        findings.append({
            "title": f"Strong correlation between '{top['col_a']}' and '{top['col_b']}' (r={top['correlation']})",
            "detail": f"{len(correlations['strong_correlations'])} notable correlation(s) found.",
            "severity": "info",
            "confidence": 0.9,
        })

    # Group differences
    if correlations["group_differences"]:
        top = correlations["group_differences"][0]
        findings.append({
            "title": f"'{top['category_col']}' groups differ significantly on '{top['numeric_col']}'",
            "detail": f"Max group mean differs {top['max_pct_diff_from_mean']}% from overall mean.",
            "severity": "info",
            "confidence": 0.8,
        })

    # Sort by severity
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    findings.sort(key=lambda x: severity_order.get(x["severity"], 3))

    return {"top_findings": findings[:6]}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: python investigate.py <data_file>", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.isfile(filepath):
        print(f"File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    print(f"[Data Detective] Loading {filepath} ...")
    df = load_data(filepath)
    print(f"[Data Detective] Loaded {len(df)} rows x {len(df.columns)} columns")

    print("[Phase 1] Scene Survey ...")
    scene = scene_survey(df)

    print("[Phase 2] Fingerprinting ...")
    fp = fingerprinting(df)

    print("[Phase 3] Anomaly Tracking ...")
    anomalies = anomaly_tracking(df)

    print("[Phase 4] Correlation Search ...")
    corr = correlation_search(df)

    print("[Phase 5] Building Summary ...")
    summary = build_summary(scene, fp, anomalies, corr)

    report = {
        "file": filepath,
        "scene_survey": scene,
        "fingerprinting": fp,
        "anomaly_tracking": anomalies,
        "correlation_search": corr,
        "summary": summary,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"[Data Detective] Findings saved to {OUTPUT_PATH}")
    print(f"[Data Detective] Top findings:")
    for i, finding in enumerate(summary["top_findings"][:3], 1):
        print(f"  {i}. [{finding['severity'].upper()}] {finding['title']}")


if __name__ == "__main__":
    main()
