# Data Dictionary — PAIMANA Flash Report Extraction

## Source Data
The PAIMANA Flash Reports are monthly PDF publications from MoSPI's Infrastructure & Project Monitoring Division (IPMD). Each report contains data on Central Sector Infrastructure Projects costing ₹150 crore and above.

## Tables in Each Flash Report

| Table | Name | Type | Use |
|---|---|---|---|
| Table 1 | Ministry-wise Ongoing Projects | Summary | Validation reference |
| Table 2 | State-wise Ongoing Projects | Summary | Validation reference |
| Table 3 | Completed Projects | Detail | Secondary extraction |
| Table 4 | Newly Added Projects | Detail | Secondary extraction |
| Table 5 | Ongoing Projects (NE Region) | Detail | Skip (subset of Table 6) |
| Table 6 | All Ongoing Projects | Detail | **Primary extraction target** |

## Raw Extracted Fields (from Table 6)

| # | Field | Source Column | Type | Description |
|---|---|---|---|---|
| 1 | `sl_no` | Sl.No | string | Serial number within the report |
| 2 | `project_name` | Project Name (compound) | string | Full project name |
| 3 | `implementing_agency` | Project Name (compound) | string | Implementing agency extracted from parentheses |
| 4 | `project_code` | Project Name (compound) | string | PAIMANA project code (e.g., "612786") |
| 5 | `legacy_ocms_code` | Project Name (compound) | string | Legacy OCMS code (e.g., "N04000106"), may be empty |
| 6 | `pmgid` | Project Name (compound) | string | PM Gati Shakti ID, may be empty |
| 7 | `state` | State | string | State / Union Territory |
| 8 | `approval_date` | Date of Approval (stacked) | string | Date of project approval (MM/YYYY) |
| 9 | `start_date` | Date of Approval (stacked) | string | Actual start date (MM/YYYY), from second line |
| 10 | `original_completion_date` | Target DoC (stacked) | string | Original target date of completion (MM/YYYY) |
| 11 | `revised_completion_date` | Target DoC (stacked) | string | Revised date of completion (MM/YYYY) |
| 12 | `original_cost_cr` | Cost (stacked) | float | Original sanctioned cost in ₹ Crore |
| 13 | `revised_cost_cr` | Cost (stacked) | float | Revised cost in ₹ Crore |
| 14 | `expenditure_cr` | Cumulative Expenditure | float | Cumulative expenditure to date in ₹ Crore |
| 15 | `physical_progress_pct` | Physical Progress (%) | float | Physical progress percentage (0-100) |
| 16 | `report_month` | Derived from filename | string | Report month (YYYY-MM) |
| 17 | `ministry` | Detected from table structure | string | Ministry/Department name |

## Compound Field Parsing

### Project Name Cell
The PDF stacks multiple values in the "Project Name" column:
```
Line 1: Project Name Text
Line 2: (Implementing Agency [ABBR])
Line 3: (Project Code)
Line 4: (Legacy OCMS Code)
Line 5: (PMGID)
```

### Date Cells
Dates are stacked as:
```
Original Date (MM/YYYY)
(Revised Date) (MM/YYYY)
```

### Cost Cell
Costs are stacked as:
```
Original Cost
(Revised Cost)
```
Both values in ₹ Crore.

## Output Files

### Per-month extraction
- `data/raw_zone/YYYY_MM_projects.parquet` — Primary output (Parquet format)
- `data/raw_zone/YYYY_MM_projects.csv` — Human-readable backup
- `data/raw_zone/extraction_logs/YYYY_MM_extraction_log.json` — Extraction metadata

### Summary
- `data/raw_zone/extraction_logs/extraction_summary.json` — Cross-report summary
