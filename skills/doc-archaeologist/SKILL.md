---
name: doc-archaeologist
description: >
  扫描项目中的文档和注释，找出过期、不一致、误导性的内容，
  生成报告并提供修复建议。当用户提到"文档过期"、"README 需要
  更新"、"注释不准确"、"文档审查"、"文档质量"时使用。
  即使用户只是说"这个项目的文档是不是有点旧了"也应触发。
---

# Doc Archaeologist

You are an expert documentation archaeologist. Your job is to scan a project's documentation and comments, find stale / inconsistent / misleading content, and produce an actionable archaeology report.

## Workflow

### Step 1 -- Scan documentation inventory

Run the scanning script to discover every documentation artifact in the target project:

```bash
python3 SKILL_DIR/scripts/scan_docs.py TARGET_DIR > /tmp/doc-arch-inventory.json
```

where `TARGET_DIR` is the root of the project the user wants analysed (default: the current working directory).

This produces a JSON inventory containing:
- All Markdown / text documentation files (README*, CONTRIBUTING*, CHANGELOG*, docs/**/*, *.md)
- Code comment metadata: Python docstrings, JSDoc blocks, TODO/FIXME/HACK/DEPRECATED markers
- Per-file metadata: path, last-modified timestamp, content sections, referenced paths, code-block commands

### Step 2 -- Analyse freshness and consistency

Feed the inventory into the analysis script:

```bash
python3 SKILL_DIR/scripts/analyze_freshness.py TARGET_DIR /tmp/doc-arch-inventory.json > /tmp/doc-arch-findings.json
```

The analyser checks:
- **Staleness**: docs that have not changed in 6+ months while the code they describe changes frequently
- **Broken references**: file paths mentioned in docs that do not exist on disk
- **Invalid commands**: shell commands in code blocks that reference binaries/scripts not found in the project
- **Environment variable drift**: env vars documented but not used in code, or used in code but not documented
- Severity levels: critical / warning / suggestion
- Each finding carries a confidence score (0.0 -- 1.0)

### Step 3 -- Generate the archaeology report

```bash
python3 SKILL_DIR/scripts/report.py TARGET_DIR /tmp/doc-arch-findings.json
```

This creates:
- `doc-archaeology-report.md` in the target directory -- the main human-readable report
- `fix-suggestions/` directory with concrete diff patches for automatically fixable issues

Report sections:
1. **Document Health Score** (A -- F letter grade)
2. **Critical Findings** -- stale docs, broken references
3. **Warnings** -- inconsistencies, drift
4. **Suggestions** -- improvements, missing docs
5. **Finding detail table**: location, problem, suggested fix, confidence

### Step 4 -- Present results

After the pipeline finishes:
1. Read `doc-archaeology-report.md` and summarise the key findings to the user.
2. If there are fix-suggestion patches, offer to apply them.
3. Answer any follow-up questions about specific findings.

## Important notes

- Always use absolute paths when invoking scripts.
- Replace `SKILL_DIR` with the actual path to this skill's directory.
- Replace `TARGET_DIR` with the project root the user wants to analyse.
- If the user does not specify a target, use the current working directory.
- The scripts require Python 3.8+.
