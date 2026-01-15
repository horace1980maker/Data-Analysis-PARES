"""
I/O module for Storyline 4.
Data loading and output writing functions.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

from .config import REQUIRED_SHEETS, OPTIONAL_SHEETS

logger = logging.getLogger(__name__)


def load_sheet(xlsx_path: str, sheet_name: str) -> pd.DataFrame:
    """
    Safe load a sheet from an Excel file.
    
    Args:
        xlsx_path: Path to Excel file
        sheet_name: Name of sheet to load
        
    Returns:
        DataFrame with normalized column names, or empty DataFrame on error
    """
    try:
        df = pd.read_excel(xlsx_path, sheet_name=sheet_name, engine="openpyxl")
        # Normalize column names for consistent processing
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
        return df
    except Exception as e:
        logger.warning(f"Could not load sheet {sheet_name}: {e}")
        return pd.DataFrame()


def load_tables(xlsx_path: str) -> Tuple[Dict[str, pd.DataFrame], List[str]]:
    """
    Load all relevant sheets and return tables plus warnings.
    
    Args:
        xlsx_path: Path to Excel file
        
    Returns:
        Tuple of (tables dict, warnings list)
    """
    tables = {}
    warnings = []
    
    try:
        xl = pd.ExcelFile(xlsx_path, engine="openpyxl")
        available_sheets = xl.sheet_names
    except Exception as e:
        logger.error(f"Failed to open Excel file: {e}")
        raise ValueError(f"Cannot open Excel file: {e}")
    
    # Load required sheets
    for sheet in REQUIRED_SHEETS:
        if sheet in available_sheets:
            df = load_sheet(xlsx_path, sheet)
            tables[sheet] = df
            logger.info(f"Loaded required sheet {sheet}: {len(df)} rows")
        else:
            tables[sheet] = pd.DataFrame()
            warnings.append(f"REQUIRED sheet missing: {sheet}")
            logger.warning(f"REQUIRED sheet missing: {sheet}")
    
    # Load optional sheets
    for sheet in OPTIONAL_SHEETS:
        if sheet in available_sheets:
            df = load_sheet(xlsx_path, sheet)
            tables[sheet] = df
            logger.info(f"Loaded optional sheet {sheet}: {len(df)} rows")
        else:
            tables[sheet] = pd.DataFrame()
            logger.debug(f"Optional sheet not found: {sheet}")
    
    return tables, warnings


def get_sheet_availability(tables: Dict[str, pd.DataFrame]) -> Dict[str, bool]:
    """
    Get availability status for each sheet.
    
    Args:
        tables: Dict of loaded tables
        
    Returns:
        Dict of sheet_name -> bool (True if not empty)
    """
    return {name: not df.empty for name, df in tables.items()}


def get_row_counts(tables: Dict[str, pd.DataFrame]) -> Dict[str, int]:
    """
    Get row counts for each non-empty sheet.
    
    Args:
        tables: Dict of loaded tables
        
    Returns:
        Dict of sheet_name -> row count
    """
    return {name: len(df) for name, df in tables.items() if not df.empty}


def create_runlog(
    input_path: str,
    output_dir: str,
    warnings: List[str],
    qa_summary: Dict[str, int],
    tables_generated: List[str],
    figures_generated: List[str],
    params: Dict[str, Any],
    sheet_availability: Dict[str, bool],
    row_counts: Dict[str, int],
    start_time: datetime,
    end_time: datetime,
) -> Dict[str, Any]:
    """
    Create a run log dictionary with execution metadata.
    
    Args:
        input_path: Path to input file
        output_dir: Output directory path
        warnings: List of warning messages
        qa_summary: QA sheet summaries
        tables_generated: Names of generated tables
        figures_generated: Names of generated figures
        params: Pipeline parameters
        sheet_availability: Sheet availability dict
        row_counts: Row counts dict
        start_time: Pipeline start time
        end_time: Pipeline end time
        
    Returns:
        Run log dictionary
    """
    return {
        "pipeline": "storyline4",
        "version": "1.0.0",
        "input_path": str(input_path),
        "output_dir": str(output_dir),
        "params": params,
        "sheet_availability": sheet_availability,
        "row_counts": row_counts,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": (end_time - start_time).total_seconds(),
        "warnings": warnings,
        "qa_summary": qa_summary,
        "outputs": {
            "tables": tables_generated,
            "figures": figures_generated,
        },
    }


def write_outputs(
    outdir: str,
    tables_dict: Dict[str, pd.DataFrame],
    figures_dict: Dict[str, str],
    report_html: str,
    runlog: Dict[str, Any],
) -> Dict[str, str]:
    """
    Write all pipeline outputs and return paths.
    
    Args:
        outdir: Output directory path
        tables_dict: Dict of output tables
        figures_dict: Dict of figure name -> file path
        report_html: HTML report content
        runlog: Run log dictionary
        
    Returns:
        Dict of output type -> path
    """
    outdir_path = Path(outdir)
    outdir_path.mkdir(parents=True, exist_ok=True)
    output_paths = {}
    
    # 1. Write tables (CSVs)
    tables_dir = outdir_path / "tables"
    tables_dir.mkdir(exist_ok=True)
    for name, df in tables_dict.items():
        if not df.empty:
            csv_path = tables_dir / f"{name}.csv"
            df.to_csv(csv_path, index=False)
            logger.debug(f"Wrote table {name} to {csv_path}")
    output_paths["tables_dir"] = str(tables_dir)
    
    # 2. Write multi-sheet Excel
    xlsx_path = outdir_path / "storyline4_outputs.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        for name, df in tables_dict.items():
            if not df.empty:
                # Truncate sheet name to 31 chars (Excel limit)
                sheet_name = name[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    output_paths["xlsx"] = str(xlsx_path)
    logger.info(f"Wrote Excel output to {xlsx_path}")
    
    # 3. Figures are already saved by plots module, just track paths
    if figures_dict:
        figures_dir = outdir_path / "figures"
        figures_dir.mkdir(exist_ok=True)
        output_paths["figures_dir"] = str(figures_dir)
    
    # 4. Report
    if report_html:
        report_dir = outdir_path / "report"
        report_dir.mkdir(exist_ok=True)
        report_path = report_dir / "storyline4.html"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_html)
        output_paths["report"] = str(report_path)
        logger.info(f"Wrote HTML report to {report_path}")
    
    # 5. Runlog
    runlog_path = outdir_path / "runlog.json"
    with open(runlog_path, "w", encoding="utf-8") as f:
        json.dump(runlog, f, indent=2, default=str)
    output_paths["runlog"] = str(runlog_path)
    logger.info(f"Wrote runlog to {runlog_path}")
    
    return output_paths
