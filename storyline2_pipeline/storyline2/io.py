#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storyline 2 I/O Module
Handles Excel loading and output writing.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .config import ALL_SHEETS, REQUIRED_SHEETS

logger = logging.getLogger(__name__)


def load_sheet(xlsx_path: str, sheet_name: str) -> pd.DataFrame:
    """
    Load a single sheet from an Excel file.
    
    Args:
        xlsx_path: Path to the Excel file
        sheet_name: Name of the sheet to load
        
    Returns:
        DataFrame with the sheet contents, or empty DataFrame if not found
    """
    try:
        df = pd.read_excel(xlsx_path, sheet_name=sheet_name, engine="openpyxl")
        # Normalize column names
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
        logger.debug(f"Loaded sheet '{sheet_name}' with {len(df)} rows, {len(df.columns)} columns")
        return df
    except Exception as e:
        logger.warning(f"Could not load sheet '{sheet_name}': {e}")
        return pd.DataFrame()


def load_tables(xlsx_path: str, sheet_list: Optional[List[str]] = None) -> Tuple[Dict[str, pd.DataFrame], List[str]]:
    """
    Load multiple sheets from an Excel file.
    
    Args:
        xlsx_path: Path to the Excel file
        sheet_list: List of sheet names to load (default: ALL_SHEETS from config)
        
    Returns:
        Tuple of (dict mapping sheet name to DataFrame, list of warnings)
    """
    if sheet_list is None:
        sheet_list = ALL_SHEETS
    
    tables: Dict[str, pd.DataFrame] = {}
    warnings: List[str] = []
    
    # Get available sheets
    try:
        xl = pd.ExcelFile(xlsx_path, engine="openpyxl")
        available_sheets = xl.sheet_names
        logger.info(f"Excel file has {len(available_sheets)} sheets")
    except Exception as e:
        logger.error(f"Failed to open Excel file: {e}")
        raise ValueError(f"Cannot open Excel file: {e}")
    
    # Load each requested sheet
    for sheet_name in sheet_list:
        if sheet_name in available_sheets:
            df = load_sheet(xlsx_path, sheet_name)
            tables[sheet_name] = df
            logger.info(f"Loaded {sheet_name}: {len(df)} rows")
        else:
            tables[sheet_name] = pd.DataFrame()
            if sheet_name in REQUIRED_SHEETS:
                warnings.append(f"REQUIRED sheet missing: {sheet_name}")
                logger.warning(f"Required sheet missing: {sheet_name}")
            else:
                logger.debug(f"Optional sheet not found: {sheet_name}")
    
    return tables, warnings


def create_runlog(
    input_path: str,
    output_dir: str,
    warnings: List[str],
    qa_summary: Dict[str, int],
    tables_generated: List[str],
    figures_generated: List[str],
    params: Dict[str, Any],
    scenarios: List[str],
    sheet_availability: Dict[str, bool],
    row_counts: Dict[str, int],
    start_time: datetime,
    end_time: datetime,
) -> Dict[str, Any]:
    """
    Create a run log dictionary with execution metadata.
    
    Returns:
        Dict containing all run information
    """
    return {
        "pipeline": "storyline2",
        "version": "1.0.0",
        "input_path": str(input_path),
        "output_dir": str(output_dir),
        "params": params,
        "scenarios": scenarios,
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
    report_html: Optional[str],
    runlog: Dict[str, Any],
) -> Dict[str, str]:
    """
    Write all outputs to the output directory.
    
    Args:
        outdir: Base output directory path
        tables_dict: Dict of table_name -> DataFrame
        figures_dict: Dict of figure_name -> file_path
        report_html: HTML report string (optional)
        runlog: Run log dictionary
        
    Returns:
        Dict of output type -> file path
    """
    outdir_path = Path(outdir)
    outdir_path.mkdir(parents=True, exist_ok=True)
    
    output_paths: Dict[str, str] = {}
    
    # Create subdirectories
    tables_dir = outdir_path / "tables"
    figures_dir = outdir_path / "figures"
    report_dir = outdir_path / "report"
    
    tables_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)
    report_dir.mkdir(exist_ok=True)
    
    # Write CSVs
    for name, df in tables_dict.items():
        if df is not None and not df.empty:
            csv_path = tables_dir / f"{name}.csv"
            df.to_csv(csv_path, index=False, encoding="utf-8")
            logger.debug(f"Wrote CSV: {csv_path}")
    
    # Write consolidated Excel
    xlsx_path = outdir_path / "storyline2_outputs.xlsx"
    try:
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            sheets_written = 0
            for name, df in tables_dict.items():
                if df is not None and not df.empty:
                    # Truncate sheet name to 31 chars (Excel limit)
                    sheet_name = name[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    sheets_written += 1
            
            # Ensure at least one sheet exists
            if sheets_written == 0:
                readme_df = pd.DataFrame({
                    "message": ["No data tables were generated. Check input data and warnings."]
                })
                readme_df.to_excel(writer, sheet_name="README", index=False)
        
        output_paths["xlsx"] = str(xlsx_path)
        logger.info(f"Wrote Excel workbook: {xlsx_path}")
    except Exception as e:
        logger.error(f"Failed to write Excel: {e}")
    
    # Copy/move figures (they should already be saved by plots module)
    for fig_name, fig_path in figures_dict.items():
        if Path(fig_path).exists():
            # Figures are already in the right place
            pass
        else:
            logger.warning(f"Figure file not found: {fig_path}")
    
    # Write HTML report
    if report_html:
        report_path = report_dir / "storyline2.html"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_html)
        output_paths["report"] = str(report_path)
        logger.info(f"Wrote HTML report: {report_path}")
    
    # Write run log
    runlog_path = outdir_path / "runlog.json"
    with open(runlog_path, "w", encoding="utf-8") as f:
        json.dump(runlog, f, indent=2, ensure_ascii=False, default=str)
    output_paths["runlog"] = str(runlog_path)
    logger.info(f"Wrote run log: {runlog_path}")
    
    return output_paths
