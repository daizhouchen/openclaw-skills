#!/usr/bin/env python3
"""
Data Detective -- Report Generator
Reads investigation JSON and produces a standalone HTML report.
"""

import json
import html
import os
import sys

FINDINGS_PATH = "/tmp/data_detective_findings.json"
REPORT_PATH = "/tmp/data_detective_report.html"


def esc(text):
    """HTML-escape text."""
    return html.escape(str(text))


def severity_badge(sev):
    colors = {
        "critical": "#ff4444",
        "warning": "#ffaa00",
        "info": "#44aaff",
    }
    color = colors.get(sev, "#888")
    return f'<span style="background:{color};color:#111;padding:2px 8px;border-radius:4px;font-weight:bold;font-size:0.85em;">{sev.upper()}</span>'


def generate_html(data: dict) -> str:
    scene = data["scene_survey"]
    fp = data["fingerprinting"]
    anomalies = data["anomaly_tracking"]
    corr = data["correlation_search"]
    summary = data["summary"]

    # Build chart data
    # 1. Missing values bar chart
    missing_labels = json.dumps(list(scene["missing_pct"].keys()))
    missing_values = json.dumps(list(scene["missing_pct"].values()))

    # 2. Outlier counts
    outlier_labels = json.dumps(list(anomalies["numeric_outliers"].keys()))
    outlier_counts = json.dumps([v["iqr_outlier_count"] for v in anomalies["numeric_outliers"].values()])

    # 3. Correlation heatmap data (as bar chart of top correlations)
    corr_labels = json.dumps([f"{c['col_a']} vs {c['col_b']}" for c in corr["strong_correlations"][:8]])
    corr_values = json.dumps([c["correlation"] for c in corr["strong_correlations"][:8]])

    # 4. Distribution skewness
    dist_labels = json.dumps(list(corr["distributions"].keys()))
    dist_skew = json.dumps([v["skewness"] for v in corr["distributions"].values()])

    # Findings HTML
    findings_html = ""
    for f in summary["top_findings"]:
        findings_html += f"""
        <div class="finding-card">
            {severity_badge(f['severity'])}
            <span style="margin-left:8px;font-size:0.8em;color:#999;">confidence: {f['confidence']}</span>
            <h3 style="margin:8px 0 4px 0;">{esc(f['title'])}</h3>
            <p style="color:#bbb;margin:0;">{esc(f['detail'])}</p>
        </div>"""

    # Missing values detail
    missing_detail = ""
    if scene["missing_values"]:
        rows = "".join(
            f"<tr><td>{esc(col)}</td><td>{count}</td><td>{scene['missing_pct'].get(col, 0)}%</td></tr>"
            for col, count in scene["missing_values"].items()
        )
        missing_detail = f"""
        <table class="data-table">
            <tr><th>Column</th><th>Missing Count</th><th>Missing %</th></tr>
            {rows}
        </table>"""

    # Duplicate detail
    dup_detail = ""
    if fp["duplicate_rows"] > 0:
        dup_detail = f"<p>{fp['duplicate_rows']} duplicate rows found (indices: {fp['duplicate_indices'][:10]})</p>"

    # Format issues detail
    fmt_detail = ""
    if fp["format_issues"]:
        items = ""
        for col, issues in fp["format_issues"].items():
            for iss in issues:
                items += f"<li><strong>{esc(col)}</strong>: {esc(iss)}</li>"
        fmt_detail = f"<ul>{items}</ul>"

    # Outlier detail
    outlier_detail = ""
    if anomalies["numeric_outliers"]:
        rows = ""
        for col, info in anomalies["numeric_outliers"].items():
            rows += f"""<tr>
                <td>{esc(col)}</td>
                <td>{info['iqr_outlier_count']}</td>
                <td>[{info['iqr_bounds'][0]}, {info['iqr_bounds'][1]}]</td>
                <td>{info['zscore_outlier_count']}</td>
            </tr>"""
        outlier_detail = f"""
        <table class="data-table">
            <tr><th>Column</th><th>IQR Outliers</th><th>IQR Bounds</th><th>Z-score Outliers</th></tr>
            {rows}
        </table>"""

    # Rare categories
    rare_detail = ""
    if anomalies["rare_categories"]:
        items = ""
        for col, info in anomalies["rare_categories"].items():
            vals = ", ".join(f"'{v}' ({p}%)" for v, p in zip(info["rare_values"][:5], info["rare_pcts"][:5]))
            items += f"<li><strong>{esc(col)}</strong> ({info['total_unique']} unique): {vals}</li>"
        rare_detail = f"<ul>{items}</ul>"

    # Correlations detail
    corr_detail = ""
    if corr["strong_correlations"]:
        rows = ""
        for c in corr["strong_correlations"]:
            rows += f"<tr><td>{esc(c['col_a'])}</td><td>{esc(c['col_b'])}</td><td>{c['correlation']}</td><td>{c['strength']}</td></tr>"
        corr_detail = f"""
        <table class="data-table">
            <tr><th>Column A</th><th>Column B</th><th>r</th><th>Strength</th></tr>
            {rows}
        </table>"""

    # Group differences
    group_detail = ""
    if corr["group_differences"]:
        items = ""
        for g in corr["group_differences"][:5]:
            items += f"<li><strong>{esc(g['category_col'])}</strong> groups differ on <strong>{esc(g['numeric_col'])}</strong> by up to {g['max_pct_diff_from_mean']}%</li>"
        group_detail = f"<ul>{items}</ul>"

    # Leads section
    leads = []
    if scene["missing_values"]:
        leads.append("Investigate root cause of missing data -- are values missing at random or systematically?")
    if fp["duplicate_rows"] > 0:
        leads.append("Determine whether duplicates are data entry errors or legitimate repeated records.")
    if anomalies["numeric_outliers"]:
        leads.append("Verify outlier values with domain experts -- they could be errors or genuine extreme cases.")
    if corr["strong_correlations"]:
        leads.append("Explore strong correlations further -- could indicate redundant features or causal relationships.")
    if corr["group_differences"]:
        leads.append("Investigate group differences -- potential segmentation opportunities or confounding factors.")
    if not leads:
        leads.append("Data looks clean! Consider deeper domain-specific analysis.")

    leads_html = "".join(f"<li>{esc(l)}</li>" for l in leads)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Data Detective Report</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #121218;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    line-height: 1.6;
    padding: 20px;
    max-width: 1100px;
    margin: 0 auto;
  }}
  h1 {{
    color: #ffcc00;
    text-align: center;
    font-size: 2em;
    margin: 20px 0;
    text-shadow: 0 0 20px rgba(255,204,0,0.3);
  }}
  h1::before {{ content: "\\1F50D "; }}
  h2 {{
    color: #ffcc00;
    border-bottom: 1px solid #333;
    padding-bottom: 6px;
    margin: 24px 0 12px 0;
    cursor: pointer;
  }}
  h2:hover {{ color: #ffe066; }}
  .subtitle {{
    text-align: center;
    color: #888;
    margin-bottom: 30px;
    font-style: italic;
  }}
  .case-meta {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
  }}
  .meta-card {{
    background: #1a1a24;
    border: 1px solid #2a2a3a;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
  }}
  .meta-card .label {{ color: #888; font-size: 0.85em; }}
  .meta-card .value {{ color: #ffcc00; font-size: 1.5em; font-weight: bold; }}
  .finding-card {{
    background: #1a1a24;
    border-left: 4px solid #ffcc00;
    border-radius: 0 8px 8px 0;
    padding: 14px 18px;
    margin: 10px 0;
  }}
  .chart-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
    gap: 20px;
    margin: 16px 0;
  }}
  .chart-box {{
    background: #1a1a24;
    border: 1px solid #2a2a3a;
    border-radius: 8px;
    padding: 16px;
  }}
  .chart-box canvas {{ max-height: 300px; }}
  .data-table {{
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
    font-size: 0.9em;
  }}
  .data-table th {{
    background: #2a2a3a;
    color: #ffcc00;
    padding: 8px 12px;
    text-align: left;
  }}
  .data-table td {{
    padding: 8px 12px;
    border-bottom: 1px solid #2a2a3a;
  }}
  .section {{ margin-bottom: 16px; }}
  .section-content {{
    overflow: hidden;
    transition: max-height 0.3s ease;
  }}
  .section-content.collapsed {{ max-height: 0 !important; }}
  ul {{ padding-left: 24px; margin: 8px 0; }}
  li {{ margin: 4px 0; }}
  .leads {{
    background: #1a2418;
    border: 1px solid #2a4a2a;
    border-radius: 8px;
    padding: 16px 24px;
    margin: 16px 0;
  }}
  .footer {{
    text-align: center;
    color: #555;
    margin-top: 40px;
    font-size: 0.8em;
    border-top: 1px solid #2a2a3a;
    padding-top: 16px;
  }}
</style>
</head>
<body>

<h1>Data Detective Report</h1>
<p class="subtitle">Case File: {esc(data['file'])}</p>

<!-- Case Summary -->
<div class="case-meta">
  <div class="meta-card"><div class="label">Rows</div><div class="value">{scene['rows']}</div></div>
  <div class="meta-card"><div class="label">Columns</div><div class="value">{scene['columns']}</div></div>
  <div class="meta-card"><div class="label">Missing Cells</div><div class="value">{sum(scene['missing_values'].values()) if scene['missing_values'] else 0}</div></div>
  <div class="meta-card"><div class="label">Duplicates</div><div class="value">{fp['duplicate_rows']}</div></div>
  <div class="meta-card"><div class="label">Outlier Columns</div><div class="value">{len(anomalies['numeric_outliers'])}</div></div>
  <div class="meta-card"><div class="label">Correlations</div><div class="value">{len(corr['strong_correlations'])}</div></div>
</div>

<!-- Top Findings -->
<div class="section">
  <h2 onclick="toggleSection(this)">Case Summary -- Top Findings</h2>
  <div class="section-content">
    {findings_html if findings_html else '<p style="color:#888;">No significant findings.</p>'}
  </div>
</div>

<!-- Evidence Board -->
<div class="section">
  <h2 onclick="toggleSection(this)">Evidence Board -- Charts</h2>
  <div class="section-content">
    <div class="chart-grid">
      <div class="chart-box"><canvas id="missingChart"></canvas></div>
      <div class="chart-box"><canvas id="outlierChart"></canvas></div>
      <div class="chart-box"><canvas id="corrChart"></canvas></div>
      <div class="chart-box"><canvas id="skewChart"></canvas></div>
    </div>
  </div>
</div>

<!-- Suspect List -->
<div class="section">
  <h2 onclick="toggleSection(this)">Suspect List -- Data Quality Issues</h2>
  <div class="section-content">
    <h3 style="color:#ccc;margin:12px 0 6px;">Missing Values</h3>
    {missing_detail if missing_detail else '<p style="color:#888;">No missing values detected.</p>'}

    <h3 style="color:#ccc;margin:12px 0 6px;">Duplicate Rows</h3>
    {dup_detail if dup_detail else '<p style="color:#888;">No duplicates found.</p>'}

    <h3 style="color:#ccc;margin:12px 0 6px;">Format Inconsistencies</h3>
    {fmt_detail if fmt_detail else '<p style="color:#888;">No format issues detected.</p>'}

    <h3 style="color:#ccc;margin:12px 0 6px;">Outliers</h3>
    {outlier_detail if outlier_detail else '<p style="color:#888;">No outliers detected.</p>'}

    <h3 style="color:#ccc;margin:12px 0 6px;">Rare Categories</h3>
    {rare_detail if rare_detail else '<p style="color:#888;">No rare categories detected.</p>'}
  </div>
</div>

<!-- Correlations -->
<div class="section">
  <h2 onclick="toggleSection(this)">Cross-References -- Correlations &amp; Group Differences</h2>
  <div class="section-content">
    <h3 style="color:#ccc;margin:12px 0 6px;">Strong Correlations</h3>
    {corr_detail if corr_detail else '<p style="color:#888;">No strong correlations found.</p>'}

    <h3 style="color:#ccc;margin:12px 0 6px;">Group Differences</h3>
    {group_detail if group_detail else '<p style="color:#888;">No significant group differences found.</p>'}
  </div>
</div>

<!-- Leads -->
<div class="section">
  <h2 onclick="toggleSection(this)">Leads -- Next Steps</h2>
  <div class="section-content">
    <div class="leads">
      <ul>{leads_html}</ul>
    </div>
  </div>
</div>

<div class="footer">
  Generated by Data Detective | Powered by pandas + Chart.js
</div>

<script>
function toggleSection(header) {{
  const content = header.nextElementSibling;
  content.classList.toggle('collapsed');
}}

const chartColors = {{
  red: '#ff4444',
  yellow: '#ffcc00',
  blue: '#4488ff',
  green: '#44cc88',
  purple: '#aa66ff',
  orange: '#ff8844',
}};

const defaultOpts = {{
  responsive: true,
  plugins: {{
    legend: {{ labels: {{ color: '#ccc' }} }},
  }},
  scales: {{
    x: {{ ticks: {{ color: '#999' }}, grid: {{ color: '#2a2a3a' }} }},
    y: {{ ticks: {{ color: '#999' }}, grid: {{ color: '#2a2a3a' }} }},
  }},
}};

// Missing values chart
const missingLabels = {missing_labels};
const missingData = {missing_values};
if (missingLabels.length > 0) {{
  new Chart(document.getElementById('missingChart'), {{
    type: 'bar',
    data: {{
      labels: missingLabels,
      datasets: [{{ label: 'Missing %', data: missingData, backgroundColor: chartColors.red }}],
    }},
    options: {{ ...defaultOpts, plugins: {{ ...defaultOpts.plugins, title: {{ display: true, text: 'Missing Values (%)', color: '#ffcc00' }} }} }},
  }});
}} else {{
  document.getElementById('missingChart').parentElement.innerHTML = '<p style="color:#888;text-align:center;padding:40px;">No missing values</p>';
}}

// Outlier chart
const outlierLabels = {outlier_labels};
const outlierData = {outlier_counts};
if (outlierLabels.length > 0) {{
  new Chart(document.getElementById('outlierChart'), {{
    type: 'bar',
    data: {{
      labels: outlierLabels,
      datasets: [{{ label: 'IQR Outlier Count', data: outlierData, backgroundColor: chartColors.orange }}],
    }},
    options: {{ ...defaultOpts, plugins: {{ ...defaultOpts.plugins, title: {{ display: true, text: 'Outliers by Column', color: '#ffcc00' }} }} }},
  }});
}} else {{
  document.getElementById('outlierChart').parentElement.innerHTML = '<p style="color:#888;text-align:center;padding:40px;">No outliers detected</p>';
}}

// Correlation chart
const corrLabels = {corr_labels};
const corrData = {corr_values};
if (corrLabels.length > 0) {{
  new Chart(document.getElementById('corrChart'), {{
    type: 'bar',
    data: {{
      labels: corrLabels,
      datasets: [{{ label: 'Correlation (r)', data: corrData, backgroundColor: corrData.map(v => v > 0 ? chartColors.blue : chartColors.purple) }}],
    }},
    options: {{ ...defaultOpts, plugins: {{ ...defaultOpts.plugins, title: {{ display: true, text: 'Strong Correlations', color: '#ffcc00' }} }}, scales: {{ ...defaultOpts.scales, y: {{ ...defaultOpts.scales.y, min: -1, max: 1 }} }} }},
  }});
}} else {{
  document.getElementById('corrChart').parentElement.innerHTML = '<p style="color:#888;text-align:center;padding:40px;">No strong correlations</p>';
}}

// Skewness chart
const distLabels = {dist_labels};
const distSkew = {dist_skew};
if (distLabels.length > 0) {{
  new Chart(document.getElementById('skewChart'), {{
    type: 'bar',
    data: {{
      labels: distLabels,
      datasets: [{{ label: 'Skewness', data: distSkew, backgroundColor: distSkew.map(v => Math.abs(v) > 1 ? chartColors.red : chartColors.green) }}],
    }},
    options: {{ ...defaultOpts, plugins: {{ ...defaultOpts.plugins, title: {{ display: true, text: 'Distribution Skewness', color: '#ffcc00' }} }} }},
  }});
}} else {{
  document.getElementById('skewChart').parentElement.innerHTML = '<p style="color:#888;text-align:center;padding:40px;">No numeric distributions</p>';
}}
</script>

</body>
</html>"""


def main():
    input_path = sys.argv[1] if len(sys.argv) > 1 else FINDINGS_PATH
    if not os.path.isfile(input_path):
        print(f"Findings file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    html_content = generate_html(data)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[Data Detective] Report generated: {REPORT_PATH}")
    file_size = os.path.getsize(REPORT_PATH)
    print(f"[Data Detective] Report size: {file_size:,} bytes")


if __name__ == "__main__":
    main()
