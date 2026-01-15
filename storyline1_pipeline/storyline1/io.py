#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storyline 1 I/O Module
Handles loading Excel workbooks and writing outputs (CSV, Excel, figures, reports).
"""

import json
import logging
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .config import REQUIRED_SHEETS, OPTIONAL_SHEETS

logger = logging.getLogger(__name__)


def load_sheet(xlsx_path: str, sheet_name: str) -> pd.DataFrame:
    """
    Load a single sheet from an Excel workbook.
    
    Args:
        xlsx_path: Path to the Excel file
        sheet_name: Name of the sheet to load
        
    Returns:
        DataFrame with sheet contents, or empty DataFrame if sheet not found
    """
    try:
        df = pd.read_excel(xlsx_path, sheet_name=sheet_name, engine="openpyxl")
        logger.debug(f"Loaded sheet '{sheet_name}' with {len(df)} rows")
        return df
    except ValueError as e:
        logger.warning(f"Sheet '{sheet_name}' not found in workbook: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error loading sheet '{sheet_name}': {e}")
        return pd.DataFrame()


def load_tables(xlsx_path: str) -> Tuple[Dict[str, pd.DataFrame], List[str]]:
    """
    Load all required and optional tables from an analysis-ready workbook.
    
    Args:
        xlsx_path: Path to the Excel file
        
    Returns:
        Tuple of (tables_dict, warnings_list)
        - tables_dict: Dict mapping sheet names to DataFrames
        - warnings_list: List of warning messages for missing sheets
    """
    tables: Dict[str, pd.DataFrame] = {}
    warnings_list: List[str] = []
    
    # Get available sheet names
    try:
        xls = pd.ExcelFile(xlsx_path, engine="openpyxl")
        available_sheets = set(xls.sheet_names)
    except Exception as e:
        logger.error(f"Failed to open workbook: {e}")
        raise
    
    # Load required sheets
    for sheet_name in REQUIRED_SHEETS:
        if sheet_name in available_sheets:
            tables[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name)
            logger.info(f"Loaded required sheet: {sheet_name} ({len(tables[sheet_name])} rows)")
        else:
            tables[sheet_name] = pd.DataFrame()
            msg = f"Required sheet '{sheet_name}' not found in workbook"
            warnings_list.append(msg)
            logger.warning(msg)
    
    # Load optional sheets (QA tables)
    for sheet_name in OPTIONAL_SHEETS:
        if sheet_name in available_sheets:
            tables[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name)
            logger.info(f"Loaded optional sheet: {sheet_name} ({len(tables[sheet_name])} rows)")
        else:
            tables[sheet_name] = pd.DataFrame()
            logger.debug(f"Optional sheet '{sheet_name}' not found")
    
    return tables, warnings_list


def write_outputs(
    outdir: str,
    tables_dict: Dict[str, pd.DataFrame],
    figures_dict: Optional[Dict[str, str]] = None,
    report_html: Optional[str] = None,
    runlog_dict: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """
    Write all outputs to the specified directory.
    
    Args:
        outdir: Output directory path
        tables_dict: Dict of table_name -> DataFrame
        figures_dict: Dict of figure_name -> figure_path (already saved)
        report_html: HTML report string
        runlog_dict: Run log dictionary
        
    Returns:
        Dict mapping output type to path
    """
    outpath = Path(outdir)
    output_paths: Dict[str, str] = {}
    
    # Create directory structure
    tables_dir = outpath / "tables"
    figures_dir = outpath / "figures"
    report_dir = outpath / "report"
    
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    
    # Write CSV files
    for table_name, df in tables_dict.items():
        if df is not None and not df.empty:
            csv_path = tables_dir / f"{table_name}.csv"
            df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            logger.info(f"Wrote CSV: {csv_path}")
            output_paths[f"csv_{table_name}"] = str(csv_path)
    
    # Write consolidated Excel workbook
    xlsx_path = outpath / "storyline1_outputs.xlsx"
    
    # Count non-empty tables
    non_empty_tables = {k: v for k, v in tables_dict.items() if v is not None and not v.empty}
    
    if non_empty_tables:
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            for table_name, df in non_empty_tables.items():
                # Truncate sheet name to 31 chars (Excel limit)
                sheet_name = table_name[:31] if len(table_name) > 31 else table_name
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        logger.info(f"Wrote Excel workbook: {xlsx_path} ({len(non_empty_tables)} sheets)")
        output_paths["xlsx"] = str(xlsx_path)
    else:
        # No non-empty tables - create a placeholder workbook
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            pd.DataFrame({"message": ["No data was generated. Check input file and warnings."]}).to_excel(
                writer, sheet_name="README", index=False
            )
        logger.warning(f"Wrote empty placeholder Excel workbook: {xlsx_path}")
        output_paths["xlsx"] = str(xlsx_path)
    
    # Record figure paths (figures are written by plots.py)
    if figures_dict:
        for fig_name, fig_path in figures_dict.items():
            output_paths[f"figure_{fig_name}"] = fig_path
    
    # Write HTML report
    if report_html:
        report_path = report_dir / "storyline1.html"
        report_path.write_text(report_html, encoding="utf-8")
        logger.info(f"Wrote HTML report: {report_path}")
        output_paths["report"] = str(report_path)
    
    # Write run log
    if runlog_dict:
        runlog_path = outpath / "runlog.json"
        with open(runlog_path, "w", encoding="utf-8") as f:
            json.dump(runlog_dict, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Wrote run log: {runlog_path}")
        output_paths["runlog"] = str(runlog_path)
    
    return output_paths


def create_runlog(
    input_path: str,
    output_dir: str,
    warnings: List[str],
    qa_summary: Dict[str, Any],
    tables_generated: List[str],
    figures_generated: List[str],
    start_time: datetime,
    end_time: datetime,
) -> Dict[str, Any]:
    """
    Create a run log dictionary with execution metadata.
    
    Args:
        input_path: Path to input workbook
        output_dir: Output directory path
        warnings: List of warning messages
        qa_summary: Summary of QA sheet contents
        tables_generated: List of generated table names
        figures_generated: List of generated figure names
        start_time: Execution start time
        end_time: Execution end time
        
    Returns:
        Run log dictionary
    """
    return {
        "pipeline": "storyline1",
        "version": "1.0.0",
        "input_path": str(input_path),
        "output_dir": str(output_dir),
        "execution": {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": (end_time - start_time).total_seconds(),
        },
        "warnings": warnings,
        "qa_summary": qa_summary,
        "outputs": {
            "tables": tables_generated,
            "figures": figures_generated,
        },
    }
