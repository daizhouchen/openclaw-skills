---
name: terminal-dashboard
description: 根据 YAML 配置生成 Rich 终端仪表盘，显示系统资源或指定服务指标。用于创建或修改终端监控界面。
---

# Terminal Dashboard Skill

Resolve `<skill_dir>` to the directory containing this `SKILL.md`. Use absolute helper paths, keep project/output paths separate, and generate only the outputs needed for the user's request.


## Workflow

### Step 1: Determine Data Sources

Identify what the user wants to monitor. Common categories:

- **System resources**: CPU, memory, disk, network, load average
- **Service health**: HTTP endpoints, database connections, Redis, message queues
- **Project status**: Git stats, CI/CD pipelines, deployment state
- **Custom metrics**: API response times, error rates, queue depths
- **Logs**: Tailing log files or journal entries

Use the specified data sources. Clarify missing requirements before adding service or network checks.

### Step 2: Generate Dashboard Script

Use `scripts/generate_dashboard.py` to produce a standalone dashboard from a YAML config:

```bash
python3 "<skill_dir>/scripts/generate_dashboard.py" <config.yaml> --output <dashboard.py>
```

The generator reads the config and emits a self-contained Python script that uses
the `rich` library for rendering. No runtime dependency on the generator itself.

Supported panel types:
- **metrics** -- Key/value cards with trend arrows (up/down)
- **progress** -- Progress bars for CPU, memory, disk, etc.
- **log** -- Scrolling tail of a log file
- **status** -- Green/yellow/red status lights for service checks

### Step 3: Configure Layout

Edit the YAML config to adjust:

- `title` -- Dashboard title shown at the top
- `refresh_interval` -- Seconds between updates (default 2)
- `layout` -- Grid arrangement, e.g. "2x2", "1x4", "3x1"
- `panels` -- List of panel definitions (type, title, sources/checks)

A default config template lives at `assets/config_template.yaml`.

### Step 4: Run and Iterate

```bash
python3 <generated_dashboard.py>
```

Use Ctrl+C to stop the dashboard. Do not leave a continuous monitor running unless requested.

### Quick Start (no config needed)

Run the bundled example dashboard directly:

```bash
python3 "<skill_dir>/scripts/dashboard_example.py"
```

This shows CPU, memory, disk, load average, and top processes out of the box.
