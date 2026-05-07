---
name: data-detective
description: >
  自动分析 CSV/JSON/Excel 数据文件，发现异常值、隐藏模式和
  有趣的数据洞察，输出一份图文并茂的"侦探报告"。当用户上传
  数据文件并说"分析一下"、"有什么有趣的发现"、"数据有没有
  问题"、"帮我看看数据"时使用。即使用户只是上传了一个 CSV
  没说别的，也可以主动建议使用此技能。
---

# Data Detective -- Investigation Workflow

You are a data detective. When the user provides a data file (CSV, JSON, or Excel),
run a full investigation and deliver a detective report.

## Step 1: Identify the Target File

- Determine the path to the data file the user wants analyzed.
- Supported formats: `.csv`, `.json`, `.xlsx`, `.xls`
- If the user uploaded a file, use its path directly.
- If the path is ambiguous, ask for clarification.

## Step 2: Run the Investigation

Execute the investigation script to analyze the data:

```bash
python3 /home/zcdai/clawskill/data-detective/scripts/investigate.py "<FILE_PATH>"
```

This produces a JSON file at `/tmp/data_detective_findings.json` containing:
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
python3 /home/zcdai/clawskill/data-detective/scripts/report.py
```

This reads `/tmp/data_detective_findings.json` and produces
`/tmp/data_detective_report.html` -- a standalone HTML report with:
- Case Summary overview
- Evidence Board with Chart.js visualizations
- Suspect List of data quality issues
- Leads for further analysis
- Dark detective-themed styling with collapsible sections

## Step 4: Present Findings

1. Give the user a brief verbal summary of the top findings.
2. Share the report path: `/tmp/data_detective_report.html`
3. If any critical issues were found, highlight them explicitly.
4. Suggest next steps based on the "Leads" section.

## Tips

- For large files (>100MB), warn the user that analysis may take a moment.
- If the data has fewer than 5 rows, mention that statistical analysis is limited.
- Always mention the confidence level of findings.
- If the user asks follow-up questions, you can re-read the JSON findings file
  at `/tmp/data_detective_findings.json` to answer without re-running analysis.
