"""
SIH 2026 — PS26103 | PDF Extraction Engine
============================================
Extracts project-level data from PAIMANA Flash Report PDFs.
Focuses on Table 6 ("All Ongoing Projects") — the master detail table.

Usage:
    python data/scripts/extract_report.py                    # Extract all PDFs
    python data/scripts/extract_report.py --file <path.pdf>  # Extract single PDF
    python data/scripts/extract_report.py --inspect <path>   # Inspect PDF structure only
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import pdfplumber
import yaml
from loguru import logger
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SOURCE_DIR = DATA_DIR / "source_pdfs"
RAW_DIR = DATA_DIR / "raw_zone"
LOG_DIR = RAW_DIR / "extraction_logs"
SCHEMA_PATH = DATA_DIR / "schema_map.yaml"

# Ensure output directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | {message}")
logger.add(LOG_DIR / "extraction_{time:YYYY-MM-DD}.log", level="DEBUG", rotation="10 MB")


def load_schema_map() -> dict:
    """Load the canonical schema mapping from YAML."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_report_month_from_filename(filename: str, schema_map: dict) -> str:
    """
    Derive the report month (YYYY-MM) from the PDF filename.
    Uses the filename_to_month mapping in schema_map.yaml.
    Falls back to regex parsing if not found in the map.
    """
    stem = Path(filename).stem
    mapping = schema_map.get("filename_to_month", {})

    # Direct lookup
    if stem in mapping:
        return mapping[stem]

    # Fuzzy: try stripping trailing suffixes like " (1)"
    clean_stem = re.sub(r"\s*\(\d+\)\s*$", "", stem)
    if clean_stem in mapping:
        return mapping[clean_stem]

    # Regex fallback: extract month and year from filename
    month_names = {
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12"
    }
    match = re.search(r"(\w+?)_?(\d{4})", stem, re.IGNORECASE)
    if match:
        month_str = match.group(1).lower().replace("flashreport_", "").replace("flashreport", "")
        year_str = match.group(2)
        # Try to find the month name
        for name, num in month_names.items():
            if name in month_str:
                return f"{year_str}-{num}"

    logger.warning(f"Could not determine report month for: {filename}")
    return "UNKNOWN"


# ---------------------------------------------------------------------------
# PDF Inspection
# ---------------------------------------------------------------------------

def inspect_pdf(pdf_path: str) -> dict:
    """
    Inspect a PDF to understand its structure before extraction.
    Returns metadata about pages, tables, and content.
    """
    info = {
        "file": str(pdf_path),
        "pages": 0,
        "tables_found": [],
        "text_samples": [],
    }

    with pdfplumber.open(pdf_path) as pdf:
        info["pages"] = len(pdf.pages)
        logger.info(f"PDF has {len(pdf.pages)} pages")

        # Sample first 5 pages for structure understanding
        for i, page in enumerate(pdf.pages[:5]):
            text = page.extract_text() or ""
            tables = page.extract_tables()
            info["text_samples"].append({
                "page": i + 1,
                "text_preview": text[:500],
                "table_count": len(tables),
            })

        # Scan all pages for tables (just counts)
        table_pages = []
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            if tables:
                for t_idx, table in enumerate(tables):
                    if table and len(table) > 0:
                        table_pages.append({
                            "page": i + 1,
                            "rows": len(table),
                            "cols": len(table[0]) if table[0] else 0,
                            "header_sample": table[0] if table[0] else [],
                        })
        info["tables_found"] = table_pages

    return info


# ---------------------------------------------------------------------------
# Core Extraction Logic
# ---------------------------------------------------------------------------

def is_table6_header(row: list) -> bool:
    """
    Detect if a row is the header of Table 6 (All Ongoing Projects).
    The header contains 'Sl.No' or similar in first cell and
    'Project Name' in second cell.
    """
    if not row or len(row) < 4:
        return False

    first_cell = str(row[0] or "").strip().lower()
    second_cell = str(row[1] or "").strip().lower()

    is_sl_no = any(marker in first_cell for marker in ["sl.no", "sl. no", "s.no", "sr.no", "sl."])
    is_project = "project" in second_cell and "name" in second_cell

    return is_sl_no and is_project


def is_data_row(row: list) -> bool:
    """
    Determine if a row is a valid data row (not a header, separator, or empty).
    A data row should have a numeric Sl.No in the first cell.
    """
    if not row or len(row) < 4:
        return False

    first_cell = str(row[0] or "").strip()

    # Must start with a number (the serial number)
    if not first_cell:
        return False

    # Check if first cell is numeric (possibly with dots/commas)
    clean_first = re.sub(r"[,.\s]", "", first_cell)
    return clean_first.isdigit()


def is_ministry_header_row(row: list) -> bool:
    """
    Detect ministry header rows that appear within Table 6.
    These are full-width merged rows like "Ministry of Railways" that
    separate projects by ministry.
    """
    if not row:
        return False

    # Ministry headers typically have content only in 1-2 cells
    non_empty = [str(c or "").strip() for c in row if str(c or "").strip()]
    if len(non_empty) == 0:
        return False

    # Check if the combined text looks like a ministry name
    combined = " ".join(non_empty).lower()
    ministry_markers = [
        "ministry of", "department of", "m/o ", "d/o ",
        "ministry/department", "total"
    ]

    # If combined text is a ministry marker and it's short (not a data row)
    if any(marker in combined for marker in ministry_markers):
        # And it doesn't have many numeric values (data rows have costs/progress)
        numeric_count = sum(1 for c in row if c and re.search(r"\d+\.\d+", str(c)))
        if numeric_count <= 1:
            return True

    return False


def parse_project_info(raw_text: str) -> dict:
    """
    Parse the compound 'Project Name' cell which contains:
    - Project name
    - Implementing agency (in parentheses)
    - Project code
    - Legacy OCMS code
    - PMGID

    Example input:
    "Construction of New Terminal...\n(Airport Authority of India [AAI])\n(612786)\n(N04000106)\n(-)"
    """
    if not raw_text:
        return {
            "project_name": "",
            "implementing_agency": "",
            "project_code": "",
            "legacy_ocms_code": "",
            "pmgid": "",
        }

    lines = [l.strip() for l in str(raw_text).split("\n") if l.strip()]

    result = {
        "project_name": "",
        "implementing_agency": "",
        "project_code": "",
        "legacy_ocms_code": "",
        "pmgid": "",
    }

    # Collect all parenthetical items
    parentheticals = []
    name_parts = []

    for line in lines:
        # Check if this line is purely a parenthetical value like "(612786)" or "(AAI)"
        paren_match = re.match(r"^\((.+)\)$", line.strip())
        if paren_match:
            parentheticals.append(paren_match.group(1).strip())
        else:
            # Could be part of the project name or agency embedded in brackets
            # Check for agency pattern: (Agency Name [ABBR])
            agency_match = re.search(r"\(([^)]*\[[^\]]*\][^)]*)\)", line)
            if agency_match:
                result["implementing_agency"] = agency_match.group(1).strip()
                # Remove the agency part from the name
                name_part = re.sub(r"\([^)]*\[[^\]]*\][^)]*\)", "", line).strip()
                if name_part:
                    name_parts.append(name_part)
            else:
                name_parts.append(line)

    result["project_name"] = " ".join(name_parts).strip()

    # Assign parenthetical values by position
    # Typical order: project_code, legacy_ocms_code, pmgid
    # But agency might also appear as a parenthetical
    code_like_parentheticals = []
    for p in parentheticals:
        if re.match(r"^[\w\d]+$", p) or p == "-":
            code_like_parentheticals.append(p)
        elif "[" in p:  # Agency with abbreviation like "Airport Authority of India [AAI]"
            result["implementing_agency"] = p
        elif len(p) > 20:  # Long text is likely part of name or agency
            if not result["implementing_agency"]:
                result["implementing_agency"] = p
            else:
                name_parts.append(p)
                result["project_name"] = " ".join(name_parts).strip()
        else:
            code_like_parentheticals.append(p)

    # Assign codes by position
    if len(code_like_parentheticals) >= 1:
        result["project_code"] = code_like_parentheticals[0]
    if len(code_like_parentheticals) >= 2:
        result["legacy_ocms_code"] = code_like_parentheticals[1]
    if len(code_like_parentheticals) >= 3:
        result["pmgid"] = code_like_parentheticals[2]

    # Clean up null markers
    for key in ["project_code", "legacy_ocms_code", "pmgid"]:
        if result[key] in ["-", "N.A.", "NA", "N/A", ""]:
            result[key] = ""

    return result


def parse_stacked_dates(raw_text: str) -> tuple:
    """
    Parse stacked date cells like:
    "03/2023\n(01/2024)" → ("03/2023", "01/2024")
    or "03/2023\n01/2024" → ("03/2023", "01/2024")
    """
    if not raw_text:
        return ("", "")

    text = str(raw_text).strip()
    # Find all date-like patterns (MM/YYYY)
    dates = re.findall(r"(\d{1,2}/\d{4})", text)

    if len(dates) >= 2:
        return (dates[0], dates[1])
    elif len(dates) == 1:
        return (dates[0], dates[0])  # Same date if only one present
    else:
        return (text, "")


def parse_stacked_costs(raw_text: str) -> tuple:
    """
    Parse stacked cost cells like:
    "265.91\n(265.91)" → (265.91, 265.91)
    "611.80\n611.80" → (611.80, 611.80)
    "1,234.56\n(2,345.67)" → (1234.56, 2345.67)
    """
    if not raw_text:
        return (None, None)

    text = str(raw_text).strip()
    # Find all numeric values (with optional commas and decimals)
    numbers = re.findall(r"[\d,]+\.?\d*", text)

    parsed = []
    for n in numbers:
        try:
            parsed.append(float(n.replace(",", "")))
        except ValueError:
            continue

    if len(parsed) >= 2:
        return (parsed[0], parsed[1])
    elif len(parsed) == 1:
        return (parsed[0], parsed[0])
    else:
        return (None, None)


def parse_expenditure(raw_text: str) -> float:
    """Parse a single numeric expenditure value."""
    if not raw_text:
        return None

    text = str(raw_text).strip()
    # Remove currency symbols, commas, whitespace
    cleaned = re.sub(r"[₹,\s]", "", text)
    # Extract the number
    match = re.search(r"([\d.]+)", cleaned)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def parse_progress(raw_text: str) -> float:
    """Parse physical progress percentage."""
    if not raw_text:
        return None

    text = str(raw_text).strip()
    # Remove % sign and whitespace
    cleaned = text.replace("%", "").replace(" ", "")
    try:
        val = float(cleaned)
        # Clip to valid range
        return max(0.0, min(100.0, val))
    except ValueError:
        return None


def extract_table6_from_page(page, page_num: int) -> list:
    """
    Extract Table 6 data rows from a single page.
    Returns a list of raw row lists.
    """
    tables = page.extract_tables()
    data_rows = []

    for table in tables:
        if not table:
            continue
        for row in table:
            if not row:
                continue
            # Skip headers and ministry separator rows
            if is_table6_header(row):
                continue
            if is_ministry_header_row(row):
                continue
            if is_data_row(row):
                data_rows.append(row)

    return data_rows


def process_raw_row(row: list, current_ministry: str, report_month: str) -> dict:
    """
    Convert a raw extracted row into a structured record
    with canonical column names.
    """
    # Ensure we have enough columns (pad if needed)
    while len(row) < 8:
        row.append("")

    # Parse compound fields
    project_info = parse_project_info(row[1])
    approval_date, start_date = parse_stacked_dates(row[3])
    original_doc, revised_doc = parse_stacked_dates(row[4])
    original_cost, revised_cost = parse_stacked_costs(row[5])
    expenditure = parse_expenditure(row[6])
    progress = parse_progress(row[7])

    return {
        "sl_no": str(row[0] or "").strip(),
        "project_name": project_info["project_name"],
        "implementing_agency": project_info["implementing_agency"],
        "project_code": project_info["project_code"],
        "legacy_ocms_code": project_info["legacy_ocms_code"],
        "pmgid": project_info["pmgid"],
        "state": str(row[2] or "").strip(),
        "approval_date": approval_date,
        "start_date": start_date,
        "original_completion_date": original_doc,
        "revised_completion_date": revised_doc,
        "original_cost_cr": original_cost,
        "revised_cost_cr": revised_cost,
        "expenditure_cr": expenditure,
        "physical_progress_pct": progress,
        "report_month": report_month,
        "ministry": current_ministry,
    }


# ---------------------------------------------------------------------------
# Main Extraction Pipeline
# ---------------------------------------------------------------------------

def find_table6_start(pdf) -> int:
    """
    Scan the PDF to find where Table 6 ("All Ongoing Projects") begins.
    Looks for the table header on pages after the summary tables.
    """
    # Table 6 typically starts around page 50-60 based on PDF analysis
    # Scan from page 20 onwards to be safe
    start_page = max(0, 20)

    for i in range(start_page, len(pdf.pages)):
        page = pdf.pages[i]
        text = page.extract_text() or ""

        # Look for Table 6 title or header indicators
        if "all ongoing projects" in text.lower():
            logger.info(f"Found 'All Ongoing Projects' text on page {i + 1}")
            return i

        # Also check for the actual table header
        tables = page.extract_tables()
        for table in (tables or []):
            for row in (table or []):
                if is_table6_header(row):
                    logger.info(f"Found Table 6 header on page {i + 1}")
                    return i

    # Fallback: start from page 50
    logger.warning("Could not definitively locate Table 6 start, defaulting to page 50")
    return 50


def extract_report(pdf_path: str, schema_map: dict) -> dict:
    """
    Extract all project data from a single PAIMANA Flash Report PDF.

    Returns:
        dict with keys: 'data' (list of records), 'metadata' (extraction stats)
    """
    filename = Path(pdf_path).name
    report_month = get_report_month_from_filename(filename, schema_map)
    logger.info(f"Extracting: {filename} → report_month={report_month}")

    records = []
    warnings = []
    current_ministry = ""
    pages_with_data = 0

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        logger.info(f"  Total pages: {total_pages}")

        # Find where Table 6 starts
        table6_start = find_table6_start(pdf)
        logger.info(f"  Table 6 starts at page: {table6_start + 1}")

        # Extract from Table 6 start to end of document
        for page_idx in tqdm(range(table6_start, total_pages),
                             desc=f"  Pages", unit="pg"):
            page = pdf.pages[page_idx]
            page_text = page.extract_text() or ""

            # Detect ministry headers from page text
            ministry_match = re.search(
                r"(?:Ministry\s+of|Department\s+of|M/o\s+)\s+(.+?)(?:\n|$)",
                page_text, re.IGNORECASE
            )
            if ministry_match:
                candidate = ministry_match.group(0).strip()
                # Only update if it looks like a standalone ministry line
                # (not part of project name)
                if len(candidate) < 100:
                    current_ministry = candidate

            # Extract tables from this page
            tables = page.extract_tables()
            page_had_data = False

            for table in (tables or []):
                if not table:
                    continue

                for row in table:
                    if not row:
                        continue

                    # Check for ministry header row within the table
                    if is_ministry_header_row(row):
                        combined = " ".join(
                            str(c or "").strip() for c in row if str(c or "").strip()
                        )
                        if len(combined) < 100:
                            current_ministry = combined
                        continue

                    # Skip table headers
                    if is_table6_header(row):
                        continue

                    # Process data rows
                    if is_data_row(row):
                        try:
                            record = process_raw_row(
                                row, current_ministry, report_month
                            )
                            records.append(record)
                            page_had_data = True
                        except Exception as e:
                            warnings.append({
                                "page": page_idx + 1,
                                "error": str(e),
                                "row_preview": str(row[:3]),
                            })

            if page_had_data:
                pages_with_data += 1

    metadata = {
        "filename": filename,
        "report_month": report_month,
        "total_pages": total_pages,
        "table6_start_page": table6_start + 1,
        "pages_with_data": pages_with_data,
        "rows_extracted": len(records),
        "warnings_count": len(warnings),
        "warnings": warnings[:50],  # Cap stored warnings
        "extracted_at": datetime.now().isoformat(),
    }

    logger.info(
        f"  Extracted {len(records)} rows from {pages_with_data} pages "
        f"({len(warnings)} warnings)"
    )

    return {"data": records, "metadata": metadata}


def save_extraction(result: dict, output_dir: Path, log_dir: Path):
    """Save extracted data to Parquet/CSV and extraction log to JSON."""
    report_month = result["metadata"]["report_month"]
    safe_month = report_month.replace("-", "_")

    # Save data
    df = pd.DataFrame(result["data"])
    if not df.empty:
        # Parquet (primary)
        parquet_path = output_dir / f"{safe_month}_projects.parquet"
        df.to_parquet(parquet_path, index=False, engine="pyarrow")
        logger.info(f"  Saved: {parquet_path.name} ({len(df)} rows)")

        # CSV (human-readable backup)
        csv_path = output_dir / f"{safe_month}_projects.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        logger.info(f"  Saved: {csv_path.name}")
    else:
        logger.warning(f"  No data extracted for {report_month}!")

    # Save extraction log
    log_path = log_dir / f"{safe_month}_extraction_log.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(result["metadata"], f, indent=2, ensure_ascii=False)

    return df


# ---------------------------------------------------------------------------
# Batch Extraction
# ---------------------------------------------------------------------------

def find_source_pdfs(source_dir: Path) -> list:
    """Find all Flash Report PDFs in the source directory."""
    patterns = ["FlashReport*.pdf", "flash_report*.pdf", "flashreport*.pdf"]
    pdfs = []
    for pattern in patterns:
        pdfs.extend(source_dir.glob(pattern))

    # Also check parent directory (PDFs might not be in source_pdfs/ yet)
    if not pdfs:
        parent = source_dir.parent.parent  # Go up to project root
        for pattern in patterns:
            pdfs.extend(parent.glob(pattern))

    # Deduplicate
    pdfs = list(set(pdfs))
    pdfs.sort(key=lambda p: p.name)
    return pdfs


def extract_all_reports(source_dir: Path = None):
    """
    Extract all Flash Report PDFs found in the source directory.
    Saves individual Parquet + CSV files per month and a combined summary.
    """
    schema_map = load_schema_map()

    if source_dir is None:
        source_dir = SOURCE_DIR

    # Find PDFs — check both source_pdfs/ and project root
    pdfs = find_source_pdfs(source_dir)
    if not pdfs:
        # Check in the project root or a 'New folder' location
        alt_dirs = [
            PROJECT_ROOT,
            Path(r"c:\Users\Hp\Desktop\New folder"),
        ]
        for alt_dir in alt_dirs:
            pdfs = list(alt_dir.glob("FlashReport*.pdf"))
            if pdfs:
                logger.info(f"Found PDFs in: {alt_dir}")
                break

    if not pdfs:
        logger.error("No Flash Report PDFs found! Place them in data/source_pdfs/")
        return

    logger.info(f"Found {len(pdfs)} Flash Report PDFs")

    all_dfs = []
    all_metadata = []

    for pdf_path in pdfs:
        try:
            result = extract_report(str(pdf_path), schema_map)
            df = save_extraction(result, RAW_DIR, LOG_DIR)
            if not df.empty:
                all_dfs.append(df)
            all_metadata.append(result["metadata"])
        except Exception as e:
            logger.error(f"FAILED to extract {pdf_path.name}: {e}")
            all_metadata.append({
                "filename": pdf_path.name,
                "error": str(e),
                "rows_extracted": 0,
            })

    # Save combined extraction summary
    summary = {
        "total_reports": len(pdfs),
        "successful": sum(1 for m in all_metadata if "error" not in m),
        "total_rows_extracted": sum(m.get("rows_extracted", 0) for m in all_metadata),
        "per_report": all_metadata,
        "extracted_at": datetime.now().isoformat(),
    }

    summary_path = LOG_DIR / "extraction_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    logger.info("=" * 60)
    logger.info(f"EXTRACTION COMPLETE")
    logger.info(f"  Reports processed: {summary['total_reports']}")
    logger.info(f"  Successful: {summary['successful']}")
    logger.info(f"  Total rows: {summary['total_rows_extracted']}")
    logger.info(f"  Summary: {summary_path}")

    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="PAIMANA Flash Report PDF Extraction Engine"
    )
    parser.add_argument(
        "--file", type=str, help="Path to a single PDF to extract"
    )
    parser.add_argument(
        "--inspect", type=str, help="Inspect PDF structure (no extraction)"
    )
    parser.add_argument(
        "--source-dir", type=str, help="Override source PDF directory"
    )
    parser.add_argument(
        "--all", action="store_true", default=True,
        help="Extract all PDFs (default behavior)"
    )

    args = parser.parse_args()

    if args.inspect:
        logger.info(f"Inspecting: {args.inspect}")
        info = inspect_pdf(args.inspect)
        print(json.dumps(info, indent=2, default=str))
        return

    if args.file:
        schema_map = load_schema_map()
        result = extract_report(args.file, schema_map)
        save_extraction(result, RAW_DIR, LOG_DIR)
        return

    # Default: extract all
    source_dir = Path(args.source_dir) if args.source_dir else None
    extract_all_reports(source_dir)


if __name__ == "__main__":
    main()
