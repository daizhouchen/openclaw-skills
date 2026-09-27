---
name: git-storyteller
description: 分析 Git 仓库历史并生成包含时间线、贡献统计和里程碑的 HTML 报告。用于项目历史回顾或 Git 历史可视化。
---

# Git Storyteller

Resolve `<skill_dir>` to the directory containing this `SKILL.md`. Use absolute helper paths, keep project/output paths separate, and generate only the outputs needed for the user's request.


Transform a Git repository's commit history into a visual narrative HTML report.

## Workflow

Follow these steps in order:

### Step 1: Identify the Target Repository

- If the user specifies a repo path, use that.
- If the user is working inside a git repo (check with `git rev-parse --show-toplevel`), use the current repo.
- If no repo can be determined, ask the user to specify one.

### Step 2: Run the Analysis Script

Run the analysis script to collect and process git history data:

```bash
python3 "<skill_dir>/scripts/analyze.py" <repo-path>
```

This produces a `git-story-data.json` file in the current working directory containing:
- Commit log with authors, dates, messages
- Contributor statistics and rankings
- File change heatmap
- Dramatic events (late-night commits, reverts, hotfixes)
- Milestones (merge commits, tags, large refactors)
- Commit frequency over time

### Step 3: Render the HTML Report

Generate the visual HTML report from the analysis data:

```bash
python3 "<skill_dir>/scripts/render.py" [path-to-json]
```

If no JSON path is given, it reads `git-story-data.json` from the current directory.
This produces a `project-story.html` file.

### Step 4: Present the Results

Tell the user:
1. Where the HTML report was saved
2. A brief narrative summary of key findings:
   - Total commits, contributors, and time span
   - Top contributors
   - Notable dramatic events found
   - Key milestones
3. Suggest they open `project-story.html` in a browser for the full interactive experience.

## Important Notes

- The analysis limits history to the most recent 2 years to handle large repos efficiently.
- The HTML report is a single HTML file; charts require the Chart.js CDN.
- Dark theme with responsive design for comfortable viewing.
- All scripts require Python 3.7+ and Git installed on the system.
