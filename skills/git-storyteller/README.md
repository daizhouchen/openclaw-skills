> 📦 Part of [**openclaw-skills**](../../) monorepo
> Status: **experimental archive** · originally pushed 2026-03-31 ~ 2026-04-01
> One-liner: Git 历史→电影感 HTML 叙事（timeline / contributor profiles）

---

# Git Storyteller

> Turn your Git history into a cinematic project documentary -- one command, zero config.

## What Is This?

Git Storyteller is an [OpenClaw](https://openclawskill.ai) skill that transforms any Git repository's commit history into a stunning, standalone HTML narrative report. It mines your commits, contributors, tags, and file changes, then weaves them into an interactive visual story featuring timelines, leaderboards, dramatic-event detection, and code-volume charts. Just point it at a repo and get a browser-ready report -- no dashboards to deploy, no databases to configure, no API keys required.

## Demo / Preview

The generated `project-story.html` is a single-file dark-themed page you open directly in any browser. It features six summary stat cards, four interactive Chart.js charts (commit frequency, code volume, contributor breakdown, file heatmap), a scrollable contributor leaderboard with medal icons, color-coded dramatic-event cards in a responsive grid, and a vertical milestone timeline with colored dots for tags, merges, and large changes. Fully responsive on mobile and desktop.

## Features

| Category | Details |
|---|---|
| **Commit Frequency Timeline** | Weekly commit counts rendered as an interactive bar chart |
| **Code Volume Chart** | Additions vs. deletions over time as a filled area chart (green/red) |
| **Contributor Leaderboard** | Top 20 contributors ranked by commit count with gold/silver/bronze medals, first and last commit dates |
| **File Change Heatmap** | Top 30 most-changed files by total line churn, displayed as a stacked horizontal bar chart (top 15 rendered) |
| **Dramatic Event Detection** | Late-night commits (22:00--06:00), reverts, hotfixes, and urgent/critical/emergency fixes -- each with distinct icon and color |
| **Milestone Tracking** | Git tags (releases), merge commits, and large refactors (>500 lines changed) plotted on a vertical timeline |
| **Standalone HTML** | Single `.html` file with no server needed; only external dependency is Chart.js loaded from CDN |
| **Dark Theme & Responsive** | Slate-blue dark palette with full mobile breakpoints |
| **Performance Guard** | Automatically limits analysis to the most recent 2 years (730 days) to handle large repositories |

## Installation

```bash
npx @anthropic-ai/claw@latest skill add daizhouchen/git-storyteller
```

No additional Python packages are required -- the scripts use only the Python standard library.

## Usage

### Through OpenClaw (recommended)

Simply ask in natural language:

```
> Analyze the git history of this project
> 帮我看看这个仓库的历史
> Generate a visual story for /path/to/my-repo
```

OpenClaw will run the analysis and render steps automatically, then tell you where to find the report.

### Manual CLI

```bash
# Step 1: Analyze a repository (produces git-story-data.json)
python3 scripts/analyze.py /path/to/repo

# Step 2: Render the HTML report (produces project-story.html)
python3 scripts/render.py

# Custom output location
python3 scripts/analyze.py /path/to/repo --output /tmp/data.json
python3 scripts/render.py /tmp/data.json
```

**Expected output from Step 1:**

```
Analyzing repository: /path/to/repo
History window: 2024-04-01 to present
  Parsing commit log...          Found 342 commits (excluding merges)
  Parsing merge commits...       Found 87 merge commits
  Collecting tags...             Found 12 tags
  Analyzing file changes...      Analyzed changes across 156 files
  Computing contributor stats... Found 8 contributors
  Detecting dramatic events...   Found 23 dramatic events
  Detecting milestones...        Found 41 milestones

Analysis complete! Output written to: /path/to/git-story-data.json
```

## How It Works

The skill runs a two-stage pipeline:

### Stage 1 -- `scripts/analyze.py`

Collects raw data from Git and computes derived statistics:

| Step | What It Does |
|---|---|
| **Parse commits** | Runs `git log --no-merges` with a custom format to extract hash, author, email, ISO date, subject, and parent hashes |
| **Parse merges** | Runs `git log --merges` separately to capture merge commits for milestone detection |
| **Collect tags** | Runs `git tag --sort=-creatordate` to list all version tags with their dates |
| **File numstat** | Runs `git log --numstat` to get per-file addition/deletion counts per commit |
| **Contributor stats** | Aggregates commit counts per author and tracks their first and last commit dates |
| **Commit frequency** | Buckets commits into daily counts, then rolls up to weekly aggregates |
| **Dramatic events** | Scans commit timestamps for late-night work (22:00--06:00) and commit messages for revert, hotfix, urgent, critical, and emergency keywords |
| **Milestones** | Combines tags, merge commits (limited to 50), and large-change commits (>500 lines) into a unified milestone list |
| **File heatmap** | Ranks files by total churn (additions + deletions) and keeps the top 30 |

Output: a single `git-story-data.json` file.

### Stage 2 -- `scripts/render.py`

Reads the JSON and produces a self-contained HTML report:

- Injects summary stats into card components
- Serializes chart data as inline JSON for three Chart.js charts (frequency bar, volume area, files horizontal bar)
- Builds a contributor leaderboard with proportional background bars
- Renders dramatic events as color-coded cards (moon icon for late-night, flame for hotfix, warning for urgent, revert arrow for reverts)
- Renders milestones as a vertical dot timeline color-coded by type (green for tags, blue for merges, amber for large changes)

Output: a single `project-story.html` file in the same directory as the JSON input.

## Trigger Phrases

The skill activates when the user mentions any of the following:

| Language | Phrases |
|---|---|
| Chinese | "项目历史", "git 可视化", "代码故事", "贡献分析", "项目回顾", "帮我看看这个仓库的历史" |
| English | "project history", "git visualization", "code story", "contribution analysis", "project review" |

## Output Format

The HTML report contains seven sections rendered top-to-bottom:

1. **Header** -- Repository name with a gradient background and generation date subtitle
2. **Project Overview** -- Six stat cards: total commits, contributors, lines added, lines deleted, files changed, dramatic events
3. **Commit Activity Timeline** -- Weekly commit frequency as a bar chart (Chart.js, max 20 x-axis labels, auto-rotated)
4. **Code Volume Over Time** -- Additions (green) and deletions (red) per commit as filled line charts with 0.3 tension smoothing; displays up to the last 200 commits
5. **Contributor Leaderboard** -- Top 20 contributors with rank medals, name, commit count, and a proportional background bar
6. **Most Active Files** -- Top 15 most-changed files as a stacked horizontal bar chart (additions in green, deletions in red)
7. **Dramatic Events** -- Up to 30 event cards in a responsive grid, each with type icon, colored label, date, commit subject, author, and detail
8. **Milestones** -- Up to 40 milestone entries on a vertical timeline with colored dots per type

## Project Structure

```
git-storyteller/
├── SKILL.md                # OpenClaw skill definition and workflow instructions
├── README.md               # This file
├── .gitignore              # Ignores __pycache__, node_modules, *.pyc, .env
├── scripts/
│   ├── analyze.py          # Repository analysis (Python, ~470 lines)
│   └── render.py           # HTML report renderer (Python, ~540 lines)
├── assets/                 # Reserved for future static assets
└── references/             # Reserved for reference materials
```

## Configuration / Options

| Option | Flag | Default | Description |
|---|---|---|---|
| Repository path | positional arg to `analyze.py` | (required) | Absolute or relative path to the Git repository to analyze |
| Output JSON path | `--output` / `-o` | `./git-story-data.json` | Where to write the analysis JSON |
| Input JSON path | positional arg to `render.py` | `./git-story-data.json` | Path to the JSON file produced by `analyze.py` |
| History window | hardcoded | 730 days (2 years) | Maximum lookback period; not currently user-configurable |
| Top files in heatmap | hardcoded | 30 (analysis) / 15 (chart) | Number of files tracked and rendered |
| Max dramatic events shown | hardcoded | 30 | Capped in the HTML output |
| Max milestones shown | hardcoded | 40 | Capped in the HTML output |
| Git command timeout | hardcoded | 120s (general) / 180s (log) / 300s (numstat) | Per-command subprocess timeout |

## Requirements

| Dependency | Version | Notes |
|---|---|---|
| Python | 3.7+ | Uses only standard library modules (`json`, `subprocess`, `collections`, `argparse`, `datetime`, `re`, `html`, `os`, `sys`) |
| Git | any modern version | Must be available in `PATH` |
| Browser | any modern browser | To view the generated HTML report; Chart.js 4.4.0 is loaded from `cdn.jsdelivr.net` |

No `pip install` needed. No external Python packages.

## Limitations

- **Large repositories**: History is capped at the most recent 2 years (730 days). Older commits are excluded.
- **Metadata only**: The tool never reads file contents -- it only analyzes commit messages, authors, timestamps, and line-count diffs.
- **Merge commit subjects**: Milestone detection relies on commit message text; unusual merge formats may be missed.
- **Binary files**: Binary file changes (`-` in numstat) are counted as 0 additions/0 deletions.
- **CDN dependency**: The HTML report loads Chart.js from `cdn.jsdelivr.net`. Offline viewing of charts requires a cached copy or manual bundling.
- **Single branch**: Analysis runs on the currently checked-out branch only.
- **No incremental updates**: Each run re-analyzes the full history window from scratch.

## Contributing

Contributions are welcome. To get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-idea`)
3. Make your changes and test against a few real repositories
4. Submit a pull request with a clear description of what changed and why

Please keep the zero-dependency philosophy: no external Python packages, no build steps.

## License

MIT
