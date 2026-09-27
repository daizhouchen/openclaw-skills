---
name: data-detective
description: 分析 CSV、JSON 或 Excel 文件的缺失值、重复、离群值和相关性，生成统计发现与 HTML 报告。用于数据质量检查或探索性分析。
---

# Data Detective -- Investigation Workflow

Resolve `<skill_dir>` to the directory containing this `SKILL.md`. Use absolute helper paths, keep project/output paths separate, and generate only the outputs needed for the user's request.


You are a data detective. When the user provides a data file (CSV, JSON, or Excel),
analyze the requested data. Generate the HTML report when useful for the requested investigation.

## Step 1: Identify the Target File

- Determine the path to the data file the user wants analyzed.
- Supported formats: `.csv`, `.json`, `.xlsx`, `.xls`
- If the user uploaded a file, use its path directly.
- If the path is ambiguous, ask for clarification.

Create the requested output directory first. Without `--output`, both scripts use the operating system temporary directory.

## Step 2: Run the Investigation

Execute the investigation script to analyze the data:

```bash
python3 "<skill_dir>/scripts/investigate.py" "<FILE_PATH>" --output "<output_dir>/findings.json"
```

This produces a JSON file at `<output_dir>/findings.json` containing:
- Scene survey (shape, dtypes, missing values, basic stats)
- Fingerprinting (duplicates, format consistency, encoding issues)
- Anomaly tracking (IQR outliers, Z-score outliers, rare categories)
- Correlation search (numeric correlations, group differences, distribution shapes)
- Summary (top 3 findings with severity and confidence)

If the script fails, read the error output and troubleshoot. Common issues:
- File encoding problems: try specifying encoding
- Malformed data: check the raw file content
- Memory issues with very large files: suggest sampling

## Step 3: Generate the HTML Report

```bash
python3 "<skill_dir>/scripts/report.py" "<output_dir>/findings.json" --output "<output_dir>/report.html"
```

This reads `<output_dir>/findings.json` and produces
`<output_dir>/report.html` -- a standalone HTML report with:
- Case Summary overview
- Evidence Board with Chart.js visualizations
- Suspect List of data quality issues
- Leads for further analysis
- Dark detective-themed styling with collapsible sections

## Step 4: Present Findings

1. Give the user a brief verbal summary of the top findings.
2. Share the report path: `<output_dir>/report.html`
3. If any critical issues were found, highlight them explicitly.
4. Suggest next steps based on the "Leads" section.

## Tips

- For large files (>100MB), warn the user that analysis may take a moment.
- If the data has fewer than 5 rows, mention that statistical analysis is limited.
- Always mention the confidence level of findings.
- If the user asks follow-up questions, you can re-read the JSON findings file
  at `<output_dir>/findings.json` to answer without re-running analysis.
