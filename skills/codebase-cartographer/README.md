> 📦 Part of [**openclaw-skills**](../../) monorepo
> Status: **experimental archive** · originally pushed 2026-03-31 ~ 2026-04-01
> One-liner: 代码仓→D3.js 交互式架构图 + 依赖与循环检测

---

# Codebase Cartographer

> Turn any repository into a zoomable, searchable architecture map -- navigate code like Google Maps.

Codebase Cartographer is an [OpenClaw](https://openclawskill.ai) skill for OpenClaw that scans a code repository, parses imports across multiple languages, detects circular dependencies with Tarjan's strongly connected components algorithm, and renders an interactive D3.js force-directed graph. The result is a single HTML file you can open in any browser to explore module relationships, identify hub modules, spot dead code, and understand unfamiliar codebases at a glance.

## Features

- **Multi-language import parsing** -- Python, JavaScript/TypeScript (including JSX/TSX, Vue, Svelte), Go, Java, and Kotlin
- **Interactive D3.js force-directed graph** -- zoom, pan, drag nodes, hover tooltips, click-to-inspect sidebar, and file search
- **Circular dependency detection** -- Tarjan's SCC algorithm finds all dependency cycles and highlights them in red
- **Module classification** -- automatically labels hubs, orchestrators, and island modules based on degree centrality
- **Project type detection** -- identifies frontend, backend, fullstack, or library projects from marker files and dominant language
- **Framework and package manager detection** -- recognizes Next.js, Nuxt, Angular, SvelteKit, Vite, Django, Flask, FastAPI, and more
- **Zero external Python dependencies** -- runs on the standard library alone
- **Dark-themed UI** -- sidebar with statistics panel, directory-colored legend, and badge indicators for circular/hub/orchestrator nodes

## Installation

```bash
npx @anthropic-ai/claw@latest skill add daizhouchen/codebase-cartographer
```

## Quick Start

Once the skill is installed, ask OpenClaw to map your project in natural language:

```
"Help me understand this codebase"
"Show me the architecture of this project"
"Generate a dependency map"
```

OpenClaw runs the two-step pipeline automatically and opens the resulting HTML map. You can also trigger it in Chinese (see Trigger Phrases below).

## How It Works

The skill operates as a three-phase pipeline.

### Phase 1: Repository Scan (`scripts/scan.py`)

Recursively walks the target directory, skipping common non-source directories (node_modules, .git, __pycache__, .venv, dist, build, vendor, and others). For each file it records the relative path, byte size, line count, file extension, and detected language. At the root level it checks for marker files to determine:

- **Project type** -- frontend (package.json, tsconfig.json, etc.), backend (requirements.txt, go.mod, Cargo.toml, etc.), fullstack (both), or library (heuristic fallback based on dominant language).
- **Frameworks** -- scans config files and Python dependency manifests for framework names (Django, Flask, FastAPI, Starlette, Tornado, Express, Next.js, Nuxt, Angular, SvelteKit, Vite, Go Modules, Cargo, Maven, Gradle, Mix).
- **Package managers** -- npm, yarn, pnpm, bun, pip, pipenv, poetry, pdm, go modules, cargo, bundler, composer.

Output: a JSON file (`carto_scan.json`) with the full file list, language statistics, and project metadata.

### Phase 2: Dependency Analysis (`scripts/analyze_deps.py`)

Reads the scan JSON and, for every file in a supported language, parses import statements using language-specific regex patterns. Relative imports are resolved to actual project files; external packages are ignored. The analyzer then:

1. Builds a forward and reverse adjacency list (who imports whom).
2. Runs **Tarjan's SCC algorithm** to find all strongly connected components with more than one node -- these are circular dependency cycles.
3. Computes in-degree, out-degree, and total degree for every module.
4. Classifies modules: nodes with in-degree >= 1.5x the average (and at least 2) are **hubs**; nodes with out-degree above the same threshold are **orchestrators**; nodes with zero connections are **islands**.

Output: a JSON file (`carto_deps.json`) with the full graph, cycle lists, and classified node lists.

### Phase 3: Map Rendering

The analyzer injects the dependency JSON into `assets/map_template.html`, a self-contained D3.js application. The result is a single HTML file (`carto_map.html`) with no server required -- just open it in a browser.

## Supported Languages

| Language | Extensions | Import Patterns Recognized |
|---|---|---|
| Python | `.py` | `import X`, `from X import Y` |
| JavaScript | `.js`, `.jsx` | `import ... from '...'`, `require('...')` |
| TypeScript | `.ts`, `.tsx` | `import ... from '...'`, `require('...')` |
| Vue | `.vue` | `import ... from '...'`, `require('...')` |
| Svelte | `.svelte` | `import ... from '...'`, `require('...')` |
| Go | `.go` | `import "..."`, `import ( "..." )` |
| Java | `.java` | `import pkg.Class;` |
| Kotlin | `.kt` | `import pkg.Class;` |

The scanner also recognizes 40+ file extensions for language statistics (Rust, Ruby, PHP, C/C++, C#, Swift, Scala, Dart, Elixir, Haskell, and many more), though import parsing is limited to the languages above.

## Map Interactions

| Action | Behavior |
|---|---|
| **Scroll wheel** | Zoom in/out (0.1x to 8x) |
| **Drag background** | Pan the viewport |
| **Drag node** | Reposition a module; simulation re-settles on release |
| **Hover node** | Tooltip showing file path, language, line count, in/out degree |
| **Click node** | Sidebar shows filename, language badge, degree stats, dependency and dependent lists; graph dims unrelated nodes |
| **Click background** | Deselect node and restore full graph opacity |
| **Search box** | Live filter by filename (top 20 matches); clicking a result pans to that node |
| **Sidebar dependency lists** | Click any listed file to navigate to that node |

Nodes are sized proportionally to total degree (square-root scale). Colors are assigned per directory using D3's Tableau10 palette. Circular-dependency nodes override to red with a glowing stroke. Labels appear automatically on nodes with degree >= 2.

## Module Classification

| Classification | Criteria | Interpretation |
|---|---|---|
| **Hub** | In-degree >= max(1.5x average degree, 2) | Core utilities, shared models, or base classes. Changes here ripple widely. |
| **Orchestrator** | Out-degree >= max(1.5x average degree, 2) | Entry points, controllers, or coordinators that wire subsystems together. Good starting points for reading the codebase. |
| **Island** | Total degree = 0 | No resolved import connections. May be dead code, standalone scripts, config files, or test fixtures. |

## Framework and Project Detection

The scanner checks root-level files against known markers:

- **Frontend markers**: package.json, tsconfig.json, angular.json, next.config.js/mjs, nuxt.config.js/ts, vite.config.js/ts, svelte.config.js, webpack.config.js
- **Backend markers**: requirements.txt, setup.py, pyproject.toml, Pipfile, go.mod, Cargo.toml, pom.xml, build.gradle, Gemfile, composer.json, mix.exs
- **Fullstack**: both frontend and backend markers present
- **Library**: fallback when no markers match and the dominant language is not a frontend language

Framework names are extracted from config filenames and by scanning Python dependency files (requirements.txt, pyproject.toml, setup.py, Pipfile) for known framework strings.

## Trigger Phrases

The skill activates when the user mentions anything related to understanding a codebase:

**Chinese**:
- "代码架构" / "项目结构" / "依赖关系" / "代码地图"
- "帮我看懂这个项目"
- "这个仓库好大我不知道从哪里看起"

**English**:
- "code architecture" / "project structure" / "dependency map"
- "help me understand this codebase"
- "generate an architecture map"

## Project Structure

```
codebase-cartographer/
├── SKILL.md                    # Skill definition, trigger rules, and workflow instructions
├── scripts/
│   ├── scan.py                 # Repository scanner: file classification, project/framework detection
│   └── analyze_deps.py         # Dependency graph builder, Tarjan SCC, HTML map generator
├── assets/
│   └── map_template.html       # Self-contained D3.js force-directed graph template (dark theme)
├── references/                 # Reference materials
└── README.md
```

## Requirements

- **Python 3.10+** (uses `str | None` type union syntax; no third-party packages required)
- A modern web browser (Chrome, Firefox, Safari, Edge) for viewing the generated HTML map
- D3.js v7 is loaded from CDN (`d3js.org`) when opening the map

## Limitations

- Only static import statements are parsed. Dynamic imports (`importlib.import_module`, `import()`, reflection) are not detected.
- Go import resolution uses a heuristic (last path segment match) and may produce false positives in large monorepos.
- External/third-party package imports are intentionally excluded from the graph -- only intra-project dependencies are shown.
- File contents are read only to extract import lines; no deeper AST analysis is performed.
- The HTML map loads all nodes into a single D3 force simulation, which may become sluggish for very large graphs (thousands of nodes).

## Contributing

Contributions are welcome. To add support for a new language, add a regex pattern to the `PARSERS` dict in `scripts/analyze_deps.py` and a resolve strategy in `resolve_import()`. For scanner changes, update `LANGUAGE_MAP` and the relevant marker dicts in `scripts/scan.py`.

## License

MIT
