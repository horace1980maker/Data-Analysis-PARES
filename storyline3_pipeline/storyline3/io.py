import logging
import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from .config import REQUIRED_SHEETS, OPTIONAL_SHEETS

logger = logging.getLogger(__name__)

def load_sheet(xlsx_path: str, sheet_name: str) -> pd.DataFrame:
    """Safe load a sheet from an Excel file."""
    try:
        df = pd.read_excel(xlsx_path, sheet_name=sheet_name, engine="openpyxl")
        # Normalize column names for consistent processing
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
        return df
    except Exception as e:
        logger.warning(f"Could not load sheet {sheet_name}: {e}")
        return pd.DataFrame()

def load_tables(xlsx_path: str) -> Tuple[Dict[str, pd.DataFrame], List[str]]:
    """Load all relevant sheets and return tables plus warnings."""
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
        else:
            tables[sheet] = pd.DataFrame()
            warnings.append(f"REQUIRED sheet missing: {sheet}")
        
    # Load optional sheets
    for sheet in OPTIONAL_SHEETS:
        if sheet in available_sheets:
            df = load_sheet(xlsx_path, sheet)
            tables[sheet] = df
        else:
            tables[sheet] = pd.DataFrame()
        
    return tables, warnings

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
    """Create a run log dictionary with execution metadata."""
    return {
        "pipeline": "storyline3",
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

def write_outputs(outdir: str, tables_dict: Dict[str, pd.DataFrame], figures_dict: Dict[str, str], report_html: str, runlog: Dict[str, Any]) -> Dict[str, str]:
    """Write all pipeline outputs and return paths."""
    outdir_path = Path(outdir)
    outdir_path.mkdir(parents=True, exist_ok=True)
    output_paths = {}
    
    # 1. Write tables (CSVs)
    tables_dir = outdir_path / "tables"
    tables_dir.mkdir(exist_ok=True)
    for name, df in tables_dict.items():
        if not df.empty:
            df.to_csv(tables_dir / f"{name}.csv", index=False)
            
    # 2. Write multi-sheet Excel
    xlsx_path = outdir_path / "storyline3_outputs.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        for name, df in tables_dict.items():
            if not df.empty:
                df.to_excel(writer, sheet_name=name[:31], index=False)
    output_paths["xlsx"] = str(xlsx_path)
                
    # 3. Figures (already saved by plots module usually, but we track them)
    # figures_dict contains {name: path}
    
    # 4. Report
    if report_html:
        report_dir = outdir_path / "report"
        report_dir.mkdir(exist_ok=True)
        report_path = report_dir / "storyline3.html"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_html)
        output_paths["report"] = str(report_path)
        
    # 5. Runlog
    runlog_path = outdir_path / "runlog.json"
    with open(runlog_path, "w", encoding="utf-8") as f:
        json.dump(runlog, f, indent=2, default=str)
    output_paths["runlog"] = str(runlog_path)
    
    return output_paths
