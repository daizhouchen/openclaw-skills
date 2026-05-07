> 📦 Part of [**openclaw-skills**](../../) monorepo
> Status: **experimental archive** · originally pushed 2026-03-31 ~ 2026-04-01
> One-liner: 文档过期/失效扫描 + A-F 健康分

---

# doc-archaeologist

> Unearth stale docs, broken references, and misleading comments before they mislead your team.

## Description

**doc-archaeologist** is an [OpenClaw](https://openclawskill.ai) skill for OpenClaw that performs a full archaeological dig through your project's documentation and code comments. It discovers every documentation artifact -- README files, changelogs, inline docstrings, JSDoc blocks, and TODO/FIXME markers -- then cross-references them against the actual codebase to surface staleness, broken references, invalid commands, and environment variable drift. The result is a graded health report with actionable fix suggestions.

This is a skill for the OpenClaw ecosystem, not a standalone CLI tool. Once installed, OpenClaw automatically invokes it when you mention documentation quality, outdated docs, or stale comments in conversation.

## Archaeology Pipeline

The skill runs a 4-phase pipeline, each phase feeding into the next:

### Phase 1 -- Artifact Discovery (`scan_docs.py`)

Walks the entire project tree and catalogs documentation artifacts. For each documentation file it records the path, last-modified timestamp, byte size, line count, Markdown heading sections, shell commands extracted from fenced code blocks, file path references, and environment variables mentioned in backtick notation. For each code file it extracts Python docstrings (`"""..."""` and `'''...'''`), JSDoc blocks (`/** ... */`), TODO/FIXME/HACK/DEPRECATED/XXX/BUG/NOTE/WARNING markers, and environment variable usage (`os.environ`, `process.env`, `$VAR`, etc.). Automatically skips `.git`, `node_modules`, `__pycache__`, `venv`, `dist`, `build`, `vendor`, and other non-source directories.

### Phase 2 -- Carbon Dating (`analyze_freshness.py`)

Compares each document's last-modified date against git commit activity in the surrounding code. A doc untouched for 180+ days while its sibling code has 10+ recent commits is flagged as **critical**. Fewer code changes yield a **warning**; an equally inactive area produces only a **suggestion**. Confidence scores (0.0--1.0) are attached to every finding.

### Phase 3 -- Cross-Verification (`analyze_freshness.py`)

In the same analysis pass, the script checks three additional dimensions:

- **Broken references** -- every file path mentioned in docs is tested for existence on disk. Missing targets are flagged as critical (confidence 0.8).
- **Invalid commands** -- shell commands inside fenced code blocks are parsed and the leading binary is checked against shell builtins, system PATH, and project-local scripts. Unknown commands are flagged as warnings (confidence 0.6).
- **Environment variable drift** -- env vars documented but absent from code are flagged as warnings; vars used in code but never documented are flagged as suggestions.

Additionally, DEPRECATED markers in code produce warnings, and FIXME/BUG markers produce warnings prompting resolution or issue creation.

### Phase 4 -- Report Generation (`report.py`)

Produces a human-readable Markdown report (`doc-archaeology-report.md`) and a `fix-suggestions/` directory containing individual fix recommendation files for broken references, critically stale documents, and invalid commands.

## Finding Types

| Type | Severity | Description | Example |
|------|----------|-------------|---------|
| `stale_document` | critical / warning / suggestion | Doc unchanged 180+ days while related code is active | README last touched 14 months ago, 23 code commits since |
| `broken_reference` | critical | File path in docs points to a non-existent location | `See docs/setup.md` but no such file exists |
| `invalid_command` | warning | Shell command in a code block references an unknown binary | `poetry run migrate` but `poetry` is not installed |
| `env_var_doc_only` | warning | Env var documented but never referenced in source code | `DB_HOST` in README, code uses `DATABASE_URL` |
| `env_var_undocumented` | suggestion | Env var used in code but missing from documentation | `REDIS_URL` in source, absent from README |
| `deprecated_marker` | warning | A `DEPRECATED` comment found in source code | `# DEPRECATED: use new_handler instead` |
| `fixme_marker` | warning | A `FIXME` or `BUG` comment found in source code | `// FIXME: race condition on concurrent writes` |

## Health Grade System

A letter grade from A to F is computed from a base score of 100 with deductions per finding:

| Deduction | Amount |
|-----------|--------|
| Each **critical** finding | -20 points |
| Each **warning** finding | -5 points |
| Each **suggestion** finding | -1 point |

The final score is clamped to 0--100 and mapped to a grade:

| Score | Grade | Meaning |
|-------|-------|---------|
| 90--100 | **A** | Excellent -- documentation is well-maintained and consistent |
| 80--89 | **B** | Good -- minor issues detected, mostly suggestions |
| 70--79 | **C** | Fair -- several inconsistencies or stale documents found |
| 60--69 | **D** | Poor -- significant documentation problems need attention |
| 0--59 | **F** | Critical -- documentation is severely outdated or broken |

## Installation

```bash
npx @anthropic-ai/claw@latest skill add daizhouchen/doc-archaeologist
```

## Quick Start

Once installed, simply ask OpenClaw about your documentation quality. The skill triggers automatically. You can also run the pipeline manually:

```bash
# Phase 1: Scan documentation inventory
python3 SKILL_DIR/scripts/scan_docs.py /path/to/project > /tmp/doc-arch-inventory.json

# Phase 2 & 3: Analyze freshness, references, commands, and env vars
python3 SKILL_DIR/scripts/analyze_freshness.py /path/to/project /tmp/doc-arch-inventory.json > /tmp/doc-arch-findings.json

# Phase 4: Generate the archaeology report
python3 SKILL_DIR/scripts/report.py /path/to/project /tmp/doc-arch-findings.json
```

Replace `SKILL_DIR` with the absolute path to this skill's directory and `/path/to/project` with the target project root. When invoked through OpenClaw, these paths are resolved automatically.

## How It Works

### `scripts/scan_docs.py`

Recursively walks the project directory. Identifies documentation files by name pattern (`README*`, `CONTRIBUTING*`, `CHANGELOG*`, `LICENSE*`, `CHANGES*`, `HISTORY*`, `AUTHORS*`, `MIGRATION*`), by extension (`.md`, `.rst`, `.txt`, `.adoc`, `.textile`), or by location (`docs/` subtree). For code files in 16 supported languages (Python, JavaScript, TypeScript, Java, Go, Rust, Ruby, PHP, C, C++, C#, Shell, and JSX/TSX variants), it extracts markers, docstrings, and environment variable references. Outputs a JSON inventory to stdout.

### `scripts/analyze_freshness.py`

Consumes the JSON inventory and the target directory path. Uses `git log --since` to count recent commits touching each doc's parent directory. Resolves every file path reference against the filesystem. Parses shell commands from code blocks and validates the leading binary via `shutil.which()`, built-in allowlists, and project-local file checks. Computes the symmetric difference of documented vs. coded environment variables. Outputs a JSON findings list sorted by severity (critical first).

### `scripts/report.py`

Reads the findings JSON and produces two outputs. The main report (`doc-archaeology-report.md`) contains a health score section with grade and metric table, then separate sections for critical findings, warnings, and suggestions -- each with location, problem description, suggested fix, and confidence percentage. A final "All Findings Detail" table provides a sortable overview. The `fix-suggestions/` directory receives numbered Markdown files (`fix-001-broken-ref.md`, `fix-002-stale-doc.md`, `fix-003-invalid-cmd.md`) with structured remediation guidance for each auto-fixable issue.

## Report Format

The generated `doc-archaeology-report.md` contains these sections in order:

1. **Document Health Score** -- letter grade (A--F) with a summary table of critical/warning/suggestion counts
2. **Critical Findings** -- each with location, problem description, suggested fix, and confidence
3. **Warnings** -- same structure as critical findings
4. **Suggestions** -- same structure
5. **All Findings Detail** -- a full table with columns: #, Severity, Type, Location, Confidence

## Fix Suggestions

For each fixable finding, the report generator creates a standalone Markdown file in `fix-suggestions/`:

- **Broken reference fixes** (`fix-NNN-broken-ref.md`) -- identifies the file and the dead path, suggests removal or correction
- **Stale document fixes** (`fix-NNN-stale-doc.md`) -- generated only for critically stale docs, recommends review and update
- **Invalid command fixes** (`fix-NNN-invalid-cmd.md`) -- identifies the unknown binary, suggests verification or adding install instructions

A `fix-suggestions/README.md` summary is also created listing the total count of generated suggestions.

## What Gets Scanned

**Documentation files:**
- `README*`, `CONTRIBUTING*`, `CHANGELOG*`, `LICENSE*`, `CHANGES*`, `HISTORY*`, `AUTHORS*`, `MIGRATION*`
- Any file with extension `.md`, `.rst`, `.txt`, `.adoc`, `.textile`
- Everything under a `docs/` directory

**Code comments and markers (16 languages):**
- Python docstrings (`"""..."""` and `'''...'''`)
- JSDoc blocks (`/** ... */`) in JavaScript and TypeScript
- Inline markers: `TODO`, `FIXME`, `HACK`, `DEPRECATED`, `XXX`, `BUG`, `NOTE`, `WARNING`

**Cross-references extracted from docs:**
- File path references (e.g., `./src/config.py`, `docs/api.md`)
- Shell commands from fenced code blocks (` ```bash `, ` ```sh `, ` ```shell `, ` ```console `, ` ```zsh `)
- Environment variables in backtick notation (e.g., `` `DATABASE_URL` ``)

**Code-side environment variable patterns:**
- `os.environ["VAR"]`, `os.environ.get("VAR")`, `os.getenv("VAR")`
- `process.env.VAR`
- `${VAR}` and `$VAR` in shell scripts

## Trigger Phrases

The skill activates when OpenClaw detects documentation-related intent:

**Chinese:** "文档过期", "README 需要更新", "注释不准确", "文档审查", "文档质量", "这个项目的文档是不是有点旧了"

**English:** "docs are outdated", "README needs updating", "comments are inaccurate", "documentation review", "documentation quality", "are these docs stale"

## Project Structure

```
doc-archaeologist/
├── SKILL.md                        # Skill definition and workflow instructions
├── README.md                       # This file
├── .gitignore
├── scripts/
│   ├── scan_docs.py                # Phase 1: documentation inventory scanner
│   ├── analyze_freshness.py        # Phase 2-3: staleness and consistency analyzer
│   └── report.py                   # Phase 4: report and fix suggestion generator
├── assets/                         # Static assets
└── references/                     # Reference materials
```

## Requirements

- **Python 3.8+** -- no external packages required; uses only the standard library
- **Git** -- optional but recommended; enables commit-history-based staleness detection via `git log`

## Limitations

- Comment extraction supports Python docstrings and JSDoc blocks only; other doc-comment formats (Javadoc, RustDoc, GoDoc) are not parsed for content, though markers like TODO/FIXME are still captured across all 16 supported languages.
- Command validation checks whether the leading binary exists on PATH or in the project, but does not verify arguments or actually execute the command.
- Environment variable detection relies on regex matching of common patterns; dynamically constructed variable names will not be found.
- Staleness analysis uses file modification timestamps; if a doc was reformatted without content changes, it will appear fresh.

## Contributing

Contributions are welcome. Please open an issue to discuss proposed changes before submitting a pull request.

## License

MIT
