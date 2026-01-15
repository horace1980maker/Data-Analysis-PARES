#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storyline 2 CLI Module
Command-line interface for running the analysis pipeline.
"""

import argparse
import gc
import logging
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd
from typing import Any, Dict, List

from .config import ALL_SHEETS, QA_SHEETS, REQUIRED_SHEETS, STORYLINE2_SHEETS
from .io import create_runlog, load_tables, write_outputs
from .metrics import compute_all_metrics, load_params, load_weight_scenarios
from .plots import generate_all_plots
from .report import generate_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def validate_input(tables: Dict, strict: bool) -> List[str]:
    """
    Validate loaded tables and return warnings.
    
    Args:
        tables: Dict of table_name -> DataFrame
        strict: If True, raise error on missing required sheets
        
    Returns:
        List of validation warnings
    """
    warnings = []
    
    # Check required sheets
    for sheet in REQUIRED_SHEETS:
        if tables.get(sheet, None) is None or tables[sheet].empty:
            msg = f"Required sheet missing or empty: {sheet}"
            if strict:
                raise ValueError(msg)
            warnings.append(msg)
    
    # Check at least one storyline sheet exists
    storyline_found = False
    for sheet in STORYLINE2_SHEETS:
        if not tables.get(sheet, pd.DataFrame()).empty:
            storyline_found = True
            break
    
    if not storyline_found:
        msg = "No Storyline 2 data sheets found (TIDY_3_4_*, TIDY_3_5_SE_MDV)"
        if strict:
            raise ValueError(msg)
        warnings.append(msg)
    
    return warnings


def run_pipeline(
    input_path: str,
    outdir: str,
    strict: bool = False,
    include_figures: bool = True,
    include_report: bool = True,
    top_n: int = 10,
) -> Dict[str, Any]:
    """
    Run the complete Storyline 2 analysis pipeline.
    
    Args:
        input_path: Path to input Excel file
        outdir: Output directory path
        strict: Fail on missing required sheets
        include_figures: Generate visualization figures
        include_report: Generate HTML report
        top_n: Number of top items in rankings
        
    Returns:
        Dict with run results and paths
    """
    start_time = datetime.now()
    logger.info(f"Starting Storyline 2 pipeline")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {outdir}")
    
    # Create output directory
    outdir_path = Path(outdir)
    outdir_path.mkdir(parents=True, exist_ok=True)
    
    # Load tables
    logger.info("Loading tables...")
    tables, load_warnings = load_tables(input_path)
    
    # Validate
    validation_warnings = validate_input(tables, strict)
    all_warnings = load_warnings + validation_warnings
    
    # Build sheet availability and row counts
    sheet_availability = {name: not tables.get(name, pd.DataFrame()).empty for name in ALL_SHEETS}
    row_counts = {name: len(df) for name, df in tables.items() if not df.empty}
    
    logger.info(f"Loaded {sum(sheet_availability.values())}/{len(ALL_SHEETS)} sheets")
    
    # Load params
    params = load_params()
    params["top_n"] = top_n
    
    weight_scenarios = load_weight_scenarios()
    scenario_names = list(weight_scenarios.keys())
    
    # Compute metrics
    logger.info("Computing metrics...")
    metrics_tables = compute_all_metrics(tables, top_n=top_n)
    
    # Generate figures
    figures = {}
    if include_figures:
        logger.info("Generating figures...")
        figures = generate_all_plots(metrics_tables, outdir, tables=tables)
    
    # Generate report
    report_html = None
    if include_report:
        logger.info("Generating report...")
        report_html = generate_report(
            metrics_tables,
            figures,
            input_path,
            all_warnings,
            tables=tables,
        )
    
    # Build QA summary
    qa_summary = {}
    for qa_name in QA_SHEETS:
        qa_df = tables.get(qa_name, pd.DataFrame())
        qa_summary[qa_name] = len(qa_df) if not qa_df.empty else 0
    
    # Create run log
    end_time = datetime.now()
    runlog = create_runlog(
        input_path=input_path,
        output_dir=outdir,
        warnings=all_warnings,
        qa_summary=qa_summary,
        tables_generated=list(metrics_tables.keys()),
        figures_generated=list(figures.keys()),
        params=params,
        scenarios=scenario_names,
        sheet_availability=sheet_availability,
        row_counts=row_counts,
        start_time=start_time,
        end_time=end_time,
    )
    
    # Write outputs
    logger.info("Writing outputs...")
    output_paths = write_outputs(outdir, metrics_tables, figures, report_html, runlog)
    
    # Cleanup
    tables = None
    metrics_tables = None
    gc.collect()
    
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Pipeline completed in {duration:.1f}s")
    logger.info(f"Outputs written to: {outdir}")
    
    if all_warnings:
        logger.warning(f"{len(all_warnings)} warnings occurred:")
        for w in all_warnings:
            logger.warning(f"  - {w}")
    
    return {
        "success": True,
        "duration": duration,
        "warnings": all_warnings,
        "outputs": output_paths,
        "tables_count": len(runlog["outputs"]["tables"]),
        "figures_count": len(runlog["outputs"]["figures"]),
    }


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Storyline 2: Ecosystem-Service Lifelines Analysis Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m storyline2.cli --input data.xlsx --outdir output
  python -m storyline2.cli --input data.xlsx --outdir output --include-figures --include-report
  python -m storyline2.cli --input data.xlsx --outdir output --strict --top-n 15
        """,
    )
    
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to analysis-ready Excel workbook (.xlsx)",
    )
    
    parser.add_argument(
        "--outdir", "-o",
        required=True,
        help="Output directory path",
    )
    
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Fail if required sheets are missing (default: warn and continue)",
    )
    
    parser.add_argument(
        "--no-strict",
        action="store_true",
        default=False,
        help="Continue with warnings on missing sheets (default behavior)",
    )
    
    parser.add_argument(
        "--include-figures",
        action="store_true",
        default=False,
        help="Generate PNG visualization figures",
    )
    
    parser.add_argument(
        "--include-report",
        action="store_true",
        default=False,
        help="Generate HTML diagnostic report",
    )
    
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Number of top items in rankings (default: 10)",
    )
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    if not input_path.suffix.lower() == ".xlsx":
        logger.error(f"Input must be an Excel file (.xlsx)")
        sys.exit(1)
    
    # Determine strict mode
    strict = args.strict and not args.no_strict
    
    try:
        result = run_pipeline(
            input_path=str(input_path),
            outdir=args.outdir,
            strict=strict,
            include_figures=args.include_figures,
            include_report=args.include_report,
            top_n=args.top_n,
        )
        
        if result["success"]:
            print(f"\n✅ Pipeline completed successfully!")
            print(f"   Duration: {result['duration']:.1f}s")
            print(f"   Tables: {result['tables_count']}")
            print(f"   Figures: {result['figures_count']}")
            print(f"   Warnings: {len(result['warnings'])}")
            print(f"\n   Outputs: {args.outdir}")
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
