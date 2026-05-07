> 📦 Part of [**openclaw-skills**](../../) monorepo
> Status: **experimental archive** · originally pushed 2026-03-31 ~ 2026-04-01
> One-liner: CSV/JSON 异常检测 → 侦探主题 HTML 报告

---

# Data Detective

> Toss in a data file. Get back a full forensic report with anomalies, hidden patterns, and actionable insights.

**Data Detective** is an [OpenClaw](https://openclawskill.ai) skill that turns raw data files into
detective-themed investigation reports. Point it at a CSV, JSON, or Excel file and it will run a
five-phase statistical pipeline -- scanning for missing values, duplicates, outliers, correlations,
and distribution anomalies -- then render a standalone HTML report complete with interactive
Chart.js visualizations, severity-ranked findings, and suggested next steps. Everything happens
locally; no data leaves your machine.

## Investigation Pipeline

The analysis engine (`scripts/investigate.py`) executes five sequential phases, each feeding into
the final summary.

### Phase 1 -- Scene Survey

Establishes the basic shape of the dataset: row and column counts, per-column data types, missing
value counts and percentages, and full descriptive statistics (`count`, `mean`, `std`, `min`, `25%`,
`50%`, `75%`, `max`) for every numeric column.

### Phase 2 -- Fingerprinting

Scans for structural data quality problems:

- **Duplicate rows** -- exact-match detection with index tracking (reports the first 20).
- **Whitespace inconsistencies** -- leading/trailing spaces in string columns.
- **Case-variant detection** -- counts values that differ only by capitalisation (e.g. `Electronics`
  vs `electronics`).
- **Mixed date separators** -- flags columns whose names suggest dates when both `/` and `-`
  separators appear.

### Phase 3 -- Anomaly Tracking

Applies two complementary outlier algorithms to every numeric column with at least 10 non-null
values:

- **IQR method** -- computes Q1, Q3, and the interquartile range. Values below `Q1 - 1.5 * IQR` or
  above `Q3 + 1.5 * IQR` are flagged. Reports bounds and up to 10 sample outlier values.
- **Z-score method** -- flags any value whose absolute Z-score exceeds 3 (more than three standard
  deviations from the mean). Reports count and up to 10 samples.
- **Rare category detection** -- for categorical columns with more than 2 unique values, any
  category representing less than 2% of rows is reported along with its exact percentage.

### Phase 4 -- Correlation Search

Explores relationships across variables:

- **Pearson correlation matrix** -- all numeric column pairs are evaluated; pairs with |r| > 0.5
  are kept and labelled `moderate` (0.5--0.7) or `strong` (> 0.7). Top 10 reported.
- **Category-numeric group differences** -- for each categorical column with 2--20 unique values,
  computes per-group means of every numeric column and flags cases where the maximum group mean
  deviates more than 15% from the overall mean. Top 10 reported.
- **Distribution shape analysis** -- calculates skewness and kurtosis for each numeric column and
  classifies the shape as `right-skewed` (skew > 1), `left-skewed` (skew < -1), or
  `roughly symmetric`.

### Phase 5 -- Case Summary

Aggregates findings from all previous phases into a ranked list (up to 6 entries), sorted by
severity. Each finding includes a title, descriptive detail, severity level, and a confidence score
between 0 and 1.

## Features

- Two-pass outlier detection using both IQR fences and Z-score thresholds
- Pearson correlation scanning with strength classification
- Category-numeric group difference analysis (percentage deviation from overall mean)
- Skewness and kurtosis distribution profiling
- Duplicate row detection with index reporting
- Format consistency auditing (whitespace, case variants, mixed date separators)
- Rare category flagging (< 2% frequency)
- Automatic multi-encoding CSV loading (UTF-8, Latin-1, CP1252, GBK)
- Standalone HTML report with dark detective theme and Chart.js charts
- Collapsible report sections for easy navigation
- Severity-ranked findings with confidence scores

## Installation

```bash
npx @anthropic-ai/claw@latest skill add daizhouchen/data-detective
```

## Quick Start

Once installed, simply provide a data file in conversation:

```
"Analyze this sales data" (attach sales.csv)
"这个数据有没有问题？" (attach report.xlsx)
"帮我看看数据" (attach metrics.json)
```

Or run the scripts directly from the command line:

```bash
# Step 1: Run the investigation
python3 scripts/investigate.py path/to/your_data.csv

# Step 2: Generate the HTML report
python3 scripts/report.py

# Step 3: Open the report
open /tmp/data_detective_report.html
```

The investigation writes its findings to `/tmp/data_detective_findings.json`. The report generator
reads that JSON and produces `/tmp/data_detective_report.html`.

## Report Preview

The generated HTML report uses a dark, detective-themed interface and is fully self-contained (no
external assets required beyond the Chart.js CDN). It contains five collapsible sections:

| Section | Contents |
|---|---|
| **Case Summary** | Overview cards (rows, columns, missing cells, duplicates, outlier columns, correlation count) followed by severity-badged finding cards with confidence scores |
| **Evidence Board** | Four Chart.js bar charts: Missing Values (%) per column, IQR Outlier Counts per column, Strong Correlations (r values, colour-coded by sign), and Distribution Skewness (red for |skew| > 1, green otherwise) |
| **Suspect List** | Detailed tables and lists for missing values, duplicate rows, format inconsistencies, outlier bounds with IQR and Z-score counts, and rare categories |
| **Cross-References** | Correlation table (Column A, Column B, r, Strength) and group difference list with percentage deviations |
| **Leads** | Context-aware next-step recommendations generated from the findings (e.g. investigate missing data patterns, verify outliers with domain experts) |

## Severity System

Every finding is assigned one of three severity levels:

| Level | Badge Colour | When Applied |
|---|---|---|
| **CRITICAL** | Red | Missing data > 20% in any column; duplicate rows > 5% of dataset |
| **WARNING** | Amber | Missing data 5--20%; duplicates <= 5%; format inconsistencies; outliers detected |
| **INFO** | Blue | Strong correlations found; significant group differences identified |

Findings are sorted by severity (critical first) so the most urgent issues surface at the top of
the report.

## Trigger Phrases

The skill activates when the user uploads a data file and uses phrases such as:

| Chinese | English |
|---|---|
| "分析一下" | "Analyze this data" |
| "帮我看看数据" | "Take a look at my data" |
| "数据有没有问题" | "Are there any problems with the data?" |
| "有什么有趣的发现" | "Any interesting findings?" |

Even uploading a CSV without any prompt will cause the skill to suggest itself.

## Project Structure

```
data-detective/
├── SKILL.md                 # Skill definition, trigger config, and workflow steps
├── README.md                # This file
├── .gitignore
├── scripts/
│   ├── investigate.py       # 5-phase investigation engine (pandas + numpy)
│   └── report.py            # HTML report generator (Chart.js visualizations)
├── assets/
│   └── test_data.csv        # 102-row sample dataset with planted anomalies
└── references/              # Reserved for future reference materials
```

## Supported File Formats

| Format | Extensions | Notes |
|---|---|---|
| CSV | `.csv` | Auto-tries UTF-8, Latin-1, CP1252, and GBK encodings |
| JSON | `.json` | Loaded via `pandas.read_json` (records or columnar orientation) |
| Excel | `.xlsx`, `.xls` | Loaded via `pandas.read_excel` (requires `openpyxl` or `xlrd`) |

## Sample Test Data

`assets/test_data.csv` is a 102-row synthetic sales dataset with 10 columns (`date`, `product`,
`category`, `price`, `quantity`, `revenue`, `customer_email`, `region`, `rating`, `discount_pct`).
It contains deliberately planted anomalies for testing:

- Missing values in `price`, `rating`, and `customer_email`
- Duplicate rows at the end of the file
- A negative price value (-5.00) and an anomalous price spike (999.99)
- Extreme quantity outliers (500 and 200)
- Mixed date separators (`2024-01-05` vs `2024/01/09`)
- Case inconsistency (`Electronics` vs `electronics`)

## Requirements

- Python 3.8+
- pandas (`pip install pandas`)
- numpy (installed with pandas)
- openpyxl (`pip install openpyxl`) -- only needed for `.xlsx` files

## Limitations

- Files larger than 100 MB may take noticeable time to process; the skill warns accordingly.
- Datasets with fewer than 5 rows provide limited statistical value (noted in the report).
- IQR and Z-score outlier detection require at least 10 non-null values per column.
- Correlation search requires at least 2 numeric columns.
- The HTML report loads Chart.js from a CDN, so an internet connection is needed to view charts.

## Contributing

Contributions are welcome. Fork the repository, create a feature branch, and open a pull request.
Please keep changes focused and include test coverage where applicable.

## License

MIT
