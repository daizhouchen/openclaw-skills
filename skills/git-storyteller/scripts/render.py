#!/usr/bin/env python3
"""
Git Storyteller - HTML Report Renderer

Reads the JSON analysis output from analyze.py and generates a standalone
HTML report with interactive charts, timeline, and contributor leaderboard.

Usage:
    python3 render.py [path-to-json]

If no path is given, reads git-story-data.json from the current directory.
Output: project-story.html in the same directory as the JSON input.
"""

import json
import os
import sys
from html import escape


def load_data(json_path):
    """Load analysis JSON data."""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def render_html(data):
    """Render the full HTML report as a string."""
    meta = data["meta"]
    summary = data["summary"]
    contributors = data.get("contributors", [])
    frequency = data.get("frequency", {})
    dramatic_events = data.get("dramatic_events", [])
    milestones = data.get("milestones", [])
    file_heatmap = data.get("file_heatmap", [])
    commit_sizes = data.get("commit_sizes", [])

    # Prepare chart data
    weekly_labels = json.dumps([w[0] for w in frequency.get("weekly", [])])
    weekly_values = json.dumps([w[1] for w in frequency.get("weekly", [])])

    # Commit size data for area chart
    size_labels = json.dumps([cs.get("date", "")[:10] for cs in commit_sizes])
    size_additions = json.dumps([cs["additions"] for cs in commit_sizes])
    size_deletions = json.dumps([cs["deletions"] for cs in commit_sizes])

    # Contributor chart data (top 15)
    top_contributors = contributors[:15]
    contrib_names = json.dumps([c["name"] for c in top_contributors])
    contrib_commits = json.dumps([c["commits"] for c in top_contributors])

    # File heatmap data (top 15)
    top_files = file_heatmap[:15]
    file_names = json.dumps([_truncate_path(f["file"], 40) for f in top_files])
    file_additions = json.dumps([f["additions"] for f in top_files])
    file_deletions = json.dumps([f["deletions"] for f in top_files])

    # Event type icons and colors
    event_styles = {
        "late_night": {"icon": "&#x1F319;", "color": "#6366f1", "label": "Late Night"},
        "revert": {"icon": "&#x21A9;", "color": "#ef4444", "label": "Revert"},
        "hotfix": {"icon": "&#x1F525;", "color": "#f97316", "label": "Hotfix"},
        "urgent": {"icon": "&#x26A0;", "color": "#eab308", "label": "Urgent"},
    }

    # Build dramatic events HTML
    events_html = ""
    for ev in dramatic_events[:30]:
        style = event_styles.get(ev["type"], {"icon": "&#x2022;", "color": "#888", "label": ev["type"]})
        date_short = ev.get("date", "")[:10]
        events_html += f"""
        <div class="event-card" style="border-left: 4px solid {style['color']}">
            <div class="event-header">
                <span class="event-icon">{style['icon']}</span>
                <span class="event-label" style="color:{style['color']}">{style['label']}</span>
                <span class="event-date">{escape(date_short)}</span>
            </div>
            <div class="event-subject">{escape(ev.get('subject', ''))}</div>
            <div class="event-meta">{escape(ev.get('author', ''))} &middot; {escape(ev.get('detail', ''))}</div>
        </div>
        """

    if not dramatic_events:
        events_html = '<p class="empty-state">No dramatic events detected in the analysis window.</p>'

    # Build milestones HTML
    milestones_html = ""
    milestone_types = {"tag": "#10b981", "merge": "#3b82f6", "large_change": "#f59e0b"}
    for ms in milestones[:40]:
        color = milestone_types.get(ms["type"], "#888")
        date_short = ms.get("date", "")[:10] if ms.get("date") else ""
        milestones_html += f"""
        <div class="milestone-item">
            <div class="milestone-dot" style="background:{color}"></div>
            <div class="milestone-content">
                <div class="milestone-name">{escape(ms.get('name', ''))}</div>
                <div class="milestone-detail">{escape(ms.get('detail', ''))} {escape(date_short)}</div>
            </div>
        </div>
        """

    if not milestones:
        milestones_html = '<p class="empty-state">No milestones detected.</p>'

    # Build contributor leaderboard HTML
    leaderboard_html = ""
    medals = ["&#x1F947;", "&#x1F948;", "&#x1F949;"]
    for i, c in enumerate(contributors[:20]):
        medal = medals[i] if i < 3 else f"#{i+1}"
        leaderboard_html += f"""
        <div class="contrib-row">
            <span class="contrib-rank">{medal}</span>
            <span class="contrib-name">{escape(c['name'])}</span>
            <span class="contrib-commits">{c['commits']} commits</span>
            <div class="contrib-bar" style="width:{min(100, c['commits'] / max(contributors[0]['commits'], 1) * 100):.0f}%"></div>
        </div>
        """

    repo_name = escape(meta.get("repo_name", "Unknown"))
    analysis_date = meta.get("analysis_date", "")[:10]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Git Story: {repo_name}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0f172a;
    --surface: #1e293b;
    --surface2: #334155;
    --text: #e2e8f0;
    --text-dim: #94a3b8;
    --accent: #38bdf8;
    --accent2: #818cf8;
    --green: #10b981;
    --red: #ef4444;
    --orange: #f97316;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    padding: 0;
  }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem 1.5rem; }}

  /* Header */
  .header {{
    text-align: center;
    padding: 3rem 1rem;
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border-bottom: 1px solid var(--surface2);
  }}
  .header h1 {{ font-size: 2.5rem; color: var(--accent); margin-bottom: 0.5rem; }}
  .header .subtitle {{ color: var(--text-dim); font-size: 1.1rem; }}

  /* Stats Grid */
  .stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    margin: 2rem 0;
  }}
  .stat-card {{
    background: var(--surface);
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
  }}
  .stat-value {{
    font-size: 2rem;
    font-weight: 700;
    color: var(--accent);
  }}
  .stat-label {{
    color: var(--text-dim);
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}

  /* Sections */
  .section {{
    margin: 3rem 0;
  }}
  .section h2 {{
    font-size: 1.5rem;
    color: var(--accent);
    margin-bottom: 1.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--surface2);
  }}

  /* Chart containers */
  .chart-box {{
    background: var(--surface);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
  }}
  .chart-box canvas {{
    max-height: 400px;
  }}

  /* Contributor leaderboard */
  .contrib-row {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem 1rem;
    background: var(--surface);
    border-radius: 8px;
    margin-bottom: 0.5rem;
    position: relative;
    overflow: hidden;
  }}
  .contrib-rank {{ font-size: 1.2rem; min-width: 2.5rem; text-align: center; }}
  .contrib-name {{ flex: 1; font-weight: 500; z-index: 1; }}
  .contrib-commits {{ color: var(--text-dim); font-size: 0.9rem; z-index: 1; white-space: nowrap; }}
  .contrib-bar {{
    position: absolute;
    left: 0; top: 0; bottom: 0;
    background: rgba(56, 189, 248, 0.08);
    border-radius: 8px;
    transition: width 0.3s;
  }}

  /* Event cards */
  .events-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 1rem;
  }}
  .event-card {{
    background: var(--surface);
    border-radius: 8px;
    padding: 1rem 1.25rem;
  }}
  .event-header {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.4rem;
  }}
  .event-icon {{ font-size: 1.2rem; }}
  .event-label {{ font-weight: 600; font-size: 0.85rem; text-transform: uppercase; }}
  .event-date {{ color: var(--text-dim); font-size: 0.85rem; margin-left: auto; }}
  .event-subject {{ font-weight: 500; margin-bottom: 0.3rem; word-break: break-word; }}
  .event-meta {{ color: var(--text-dim); font-size: 0.85rem; }}

  /* Milestones timeline */
  .milestones-list {{ padding-left: 1rem; }}
  .milestone-item {{
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 0.75rem 0;
    border-left: 2px solid var(--surface2);
    padding-left: 1.5rem;
    position: relative;
  }}
  .milestone-dot {{
    width: 12px; height: 12px;
    border-radius: 50%;
    position: absolute;
    left: -7px; top: 1rem;
  }}
  .milestone-content {{ flex: 1; }}
  .milestone-name {{ font-weight: 500; }}
  .milestone-detail {{ color: var(--text-dim); font-size: 0.85rem; }}

  /* Empty state */
  .empty-state {{ color: var(--text-dim); font-style: italic; padding: 2rem; text-align: center; }}

  /* Footer */
  .footer {{
    text-align: center;
    padding: 2rem;
    color: var(--text-dim);
    font-size: 0.85rem;
    border-top: 1px solid var(--surface2);
    margin-top: 3rem;
  }}

  @media (max-width: 768px) {{
    .header h1 {{ font-size: 1.8rem; }}
    .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .events-grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

<div class="header">
    <h1>{repo_name}</h1>
    <div class="subtitle">Git Repository Story &middot; Generated {escape(analysis_date)}</div>
</div>

<div class="container">

    <!-- Project Overview -->
    <div class="section">
        <h2>Project Overview</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{summary['total_commits']}</div>
                <div class="stat-label">Total Commits</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary['total_contributors']}</div>
                <div class="stat-label">Contributors</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{_format_number(summary['total_additions'])}</div>
                <div class="stat-label">Lines Added</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{_format_number(summary['total_deletions'])}</div>
                <div class="stat-label">Lines Deleted</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary['total_files_changed']}</div>
                <div class="stat-label">Files Changed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(dramatic_events)}</div>
                <div class="stat-label">Dramatic Events</div>
            </div>
        </div>
    </div>

    <!-- Commit Frequency Timeline -->
    <div class="section">
        <h2>Commit Activity Timeline</h2>
        <div class="chart-box">
            <canvas id="frequencyChart"></canvas>
        </div>
    </div>

    <!-- Code Volume Area Chart -->
    <div class="section">
        <h2>Code Volume Over Time</h2>
        <div class="chart-box">
            <canvas id="volumeChart"></canvas>
        </div>
    </div>

    <!-- Contributor Leaderboard -->
    <div class="section">
        <h2>Contributor Leaderboard</h2>
        {leaderboard_html}
    </div>

    <!-- Top Changed Files -->
    <div class="section">
        <h2>Most Active Files</h2>
        <div class="chart-box">
            <canvas id="filesChart"></canvas>
        </div>
    </div>

    <!-- Dramatic Events -->
    <div class="section">
        <h2>Dramatic Events</h2>
        <div class="events-grid">
            {events_html}
        </div>
    </div>

    <!-- Milestones -->
    <div class="section">
        <h2>Milestones</h2>
        <div class="milestones-list">
            {milestones_html}
        </div>
    </div>

</div>

<div class="footer">
    Generated by Git Storyteller &middot; Data from {escape(summary.get('first_commit_date', '')[:10])} to {escape(summary.get('last_commit_date', '')[:10])}
</div>

<script>
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = '#334155';

// Commit Frequency Chart
new Chart(document.getElementById('frequencyChart'), {{
    type: 'bar',
    data: {{
        labels: {weekly_labels},
        datasets: [{{
            label: 'Commits per Week',
            data: {weekly_values},
            backgroundColor: 'rgba(56, 189, 248, 0.6)',
            borderColor: 'rgba(56, 189, 248, 1)',
            borderWidth: 1,
            borderRadius: 4,
        }}]
    }},
    options: {{
        responsive: true,
        plugins: {{
            legend: {{ display: false }},
            title: {{ display: false }},
        }},
        scales: {{
            x: {{ ticks: {{ maxTicksLimit: 20, maxRotation: 45 }} }},
            y: {{ beginAtZero: true, ticks: {{ precision: 0 }} }}
        }}
    }}
}});

// Code Volume Area Chart
new Chart(document.getElementById('volumeChart'), {{
    type: 'line',
    data: {{
        labels: {size_labels},
        datasets: [
            {{
                label: 'Additions',
                data: {size_additions},
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.15)',
                fill: true,
                tension: 0.3,
                pointRadius: 1,
            }},
            {{
                label: 'Deletions',
                data: {size_deletions},
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.10)',
                fill: true,
                tension: 0.3,
                pointRadius: 1,
            }}
        ]
    }},
    options: {{
        responsive: true,
        interaction: {{ mode: 'index', intersect: false }},
        scales: {{
            x: {{ ticks: {{ maxTicksLimit: 20, maxRotation: 45 }} }},
            y: {{ beginAtZero: true }}
        }}
    }}
}});

// Top Files Chart
new Chart(document.getElementById('filesChart'), {{
    type: 'bar',
    data: {{
        labels: {file_names},
        datasets: [
            {{
                label: 'Additions',
                data: {file_additions},
                backgroundColor: 'rgba(16, 185, 129, 0.7)',
                borderRadius: 4,
            }},
            {{
                label: 'Deletions',
                data: {file_deletions},
                backgroundColor: 'rgba(239, 68, 68, 0.7)',
                borderRadius: 4,
            }}
        ]
    }},
    options: {{
        responsive: true,
        indexAxis: 'y',
        scales: {{
            x: {{ stacked: true, beginAtZero: true }},
            y: {{ stacked: true }}
        }}
    }}
}});
</script>

</body>
</html>"""

    return html


def _format_number(n):
    """Format large numbers with K/M suffix."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def _truncate_path(path, max_len):
    """Truncate a file path for display."""
    if len(path) <= max_len:
        return path
    parts = path.split("/")
    if len(parts) <= 2:
        return "..." + path[-(max_len - 3):]
    return parts[0] + "/.../" + parts[-1]


def main():
    json_path = sys.argv[1] if len(sys.argv) > 1 else "git-story-data.json"
    json_path = os.path.abspath(json_path)

    if not os.path.isfile(json_path):
        print(f"Error: JSON file not found: {json_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Reading analysis data from: {json_path}")
    data = load_data(json_path)

    print("Rendering HTML report...")
    html = render_html(data)

    output_dir = os.path.dirname(json_path)
    output_path = os.path.join(output_dir, "project-story.html")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Report generated: {output_path}")
    print(f"Open in a browser to view the interactive report.")


if __name__ == "__main__":
    main()
