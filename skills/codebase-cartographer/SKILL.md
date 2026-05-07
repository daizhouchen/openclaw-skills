---
name: codebase-cartographer
description: >
  扫描代码仓库生成交互式架构地图，展示模块依赖、调用链、
  核心入口点和代码热区。当用户提到"代码架构"、"项目结构"、
  "依赖关系"、"代码地图"、"帮我看懂这个项目"时使用。
  即使用户只是说"这个仓库好大我不知道从哪里看起"也应触发。
---

# Codebase Cartographer

Generate an interactive architecture map for any code repository.

## Workflow

### Step 1: Scan the Repository

Run the scan script to collect file metadata, detect the project type, and gather statistics.

```bash
python3 {SKILL_DIR}/scripts/scan.py <target_directory> [--output <scan_output.json>] [--exclude dir1,dir2]
```

- `<target_directory>`: The root of the repository to scan.
- `--output`: Path for the scan result JSON (default: `carto_scan.json` in the current directory).
- `--exclude`: Comma-separated list of additional directories to exclude (node_modules, .git, __pycache__, .venv, dist, build are always excluded).

The scan produces a JSON file containing:
- Full file list with sizes, languages, and line counts
- Project type detection (frontend / backend / fullstack / library)
- Framework and package manager detection
- Aggregate statistics (file counts per language, total lines, etc.)

### Step 2: Analyze Dependencies

Run the dependency analyzer on the scan output to build a dependency graph.

```bash
python3 {SKILL_DIR}/scripts/analyze_deps.py [--scan <scan_output.json>] [--output <deps_output.json>]
```

- `--scan`: Path to the scan JSON from Step 1 (default: `carto_scan.json`).
- `--output`: Path for the dependency graph JSON (default: `carto_deps.json`).

The analyzer:
- Parses imports for Python, JavaScript/TypeScript, Go, and Java
- Builds an adjacency-list dependency graph
- Detects circular dependencies using Tarjan's SCC algorithm
- Calculates in-degree and out-degree for each module
- Identifies hub modules (high in-degree), orchestrators (high out-degree), and island modules (zero connections)

### Step 3: Generate the Interactive Map

The dependency analysis script automatically generates an HTML architecture map using the D3.js template.

The generated HTML file (`carto_map.html` by default) can be opened in any browser and provides:
- Force-directed graph visualization
- Node size proportional to importance (degree centrality)
- Color-coded nodes by directory / file type
- Zoom, pan, and drag interactions
- Hover tooltips with file details
- Click-to-select with info sidebar
- Search and filter controls
- Circular dependencies highlighted in red
- Dark theme

### Interpreting the Map

After generating the map, explain the architecture to the user:

1. **Entry Points**: Files with high out-degree and low in-degree are likely entry points or orchestrators. Start here to understand the application flow.
2. **Hub Modules**: Files with high in-degree are heavily depended upon -- these are the core utilities, models, or shared libraries. Changes here have wide impact.
3. **Islands**: Files with zero connections may be dead code, standalone scripts, or configuration files.
4. **Circular Dependencies**: Highlighted in red -- these indicate tight coupling that may warrant refactoring.
5. **Clusters**: Groups of tightly connected nodes often correspond to features or subsystems.

### Quick One-Liner

To run the full pipeline:

```bash
python3 {SKILL_DIR}/scripts/scan.py <target_dir> && python3 {SKILL_DIR}/scripts/analyze_deps.py
```

Then open `carto_map.html` in a browser or provide the path to the user.
