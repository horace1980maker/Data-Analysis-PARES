"""
CLI module for Storyline 4.
Command-line interface for running the pipeline.
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

from .io import (
    create_runlog,
    get_row_counts,
    get_sheet_availability,
    load_tables,
    write_outputs,
)
from .metrics import process_metrics
from .plots import generate_plots
from .report import generate_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_params(config_path: str) -> dict:
    """Load parameters from YAML file."""
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    logger.warning(f"Config file not found: {config_path}, using defaults")
    return {}


def main(args: list = None):
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Storyline 4: Feasibility, Governance & Conflict Risk Pipeline"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to analysis-ready XLSX workbook",
    )
    parser.add_argument(
        "--outdir",
        required=True,
        help="Directory for outputs",
    )
    parser.add_argument(
        "--config",
        default="config/params.yaml",
        help="Path to params YAML file (default: config/params.yaml)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if required sheets are missing",
    )
    parser.add_argument(
        "--no-strict",
        dest="strict",
        action="store_false",
        help="Continue with warnings if sheets are missing (default)",
    )
    parser.set_defaults(strict=False)
    parser.add_argument(
        "--include-figures",
        action="store_true",
        default=True,
        help="Generate visualization figures (default: True)",
    )
    parser.add_argument(
        "--no-figures",
        dest="include_figures",
        action="store_false",
        help="Skip figure generation",
    )
    parser.add_argument(
        "--include-report",
        action="store_true",
        default=True,
        help="Generate HTML report (default: True)",
    )
    parser.add_argument(
        "--no-report",
        dest="include_report",
        action="store_false",
        help="Skip report generation",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Number of top items in rankings (default: 10)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose/debug logging",
    )
    
    parsed_args = parser.parse_args(args)
    
    if parsed_args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("Storyline 4 Pipeline: Feasibility, Governance & Conflict Risk")
    logger.info("=" * 60)
    
    # 1. Load Config
    logger.info(f"Loading config from: {parsed_args.config}")
    params = load_params(parsed_args.config)
    params["top_n"] = parsed_args.top_n
    
    # 2. Load Data
    logger.info(f"Loading data from: {parsed_args.input}")
    try:
        tables, warnings = load_tables(parsed_args.input)
    except ValueError as e:
        logger.error(f"Failed to load input file: {e}")
        sys.exit(1)
    
    sheet_availability = get_sheet_availability(tables)
    row_counts = get_row_counts(tables)
    
    logger.info(f"Loaded {len(row_counts)} non-empty sheets")
    for name, count in row_counts.items():
        logger.debug(f"  - {name}: {count} rows")
    
    # QA Summary
    qa_summary = {}
    for sheet_name in ["QA_INPUT_SCHEMA", "QA_PK_DUPLICATES", "QA_MISSING_IDS", "QA_FOREIGN_KEYS"]:
        qa_df = tables.get(sheet_name, pd.DataFrame())
        if not qa_df.empty:
            qa_summary[sheet_name] = len(qa_df)
    
    # Strict validation
    if parsed_args.strict:
        required_present = all(
            not tables.get(s, pd.DataFrame()).empty
            for s in ["LOOKUP_CONTEXT", "LOOKUP_GEO"]
        )
        data_present = any(
            not tables.get(s, pd.DataFrame()).empty
            for s in ["TIDY_5_1_ACTORES", "TIDY_5_2_DIALOGO", "TIDY_6_1_CONFLICT_EVENTS"]
        )
        
        if not required_present:
            logger.error("Strict mode: Missing required lookup sheets (LOOKUP_CONTEXT, LOOKUP_GEO)")
            sys.exit(1)
        if not data_present:
            logger.error("Strict mode: No actor, dialogue, or conflict data sheets found")
            sys.exit(1)
    
    # 3. Process Metrics
    logger.info("Computing metrics...")
    metrics = process_metrics(tables, params)
    logger.info(f"Computed {len(metrics)} metrics tables")
    
    # 4. Generate Visualizations
    figures = {}
    if parsed_args.include_figures:
        logger.info("Generating plots...")
        figures = generate_plots(metrics, parsed_args.outdir, params)
        logger.info(f"Generated {len(figures)} figures")
    
    # 5. Generate Report
    report_html = ""
    if parsed_args.include_report:
        logger.info("Generating HTML report...")
        report_html = generate_report(
            metrics,
            figures,
            parsed_args.input,
            warnings,
            tables,
        )
    
    # 6. Create Runlog
    end_time = datetime.now()
    runlog = create_runlog(
        input_path=parsed_args.input,
        output_dir=parsed_args.outdir,
        warnings=warnings,
        qa_summary=qa_summary,
        tables_generated=list(metrics.keys()),
        figures_generated=list(figures.keys()),
        params=params,
        sheet_availability=sheet_availability,
        row_counts=row_counts,
        start_time=start_time,
        end_time=end_time,
    )
    
    # 7. Write Outputs
    logger.info(f"Writing outputs to: {parsed_args.outdir}")
    output_paths = write_outputs(
        parsed_args.outdir,
        metrics,
        figures,
        report_html,
        runlog,
    )
    
    # Summary
    duration = (end_time - start_time).total_seconds()
    logger.info("=" * 60)
    logger.info("Pipeline completed successfully!")
    logger.info(f"Duration: {duration:.2f} seconds")
    logger.info(f"Tables generated: {len(metrics)}")
    logger.info(f"Figures generated: {len(figures)}")
    if warnings:
        logger.warning(f"Warnings: {len(warnings)}")
        for w in warnings:
            logger.warning(f"  - {w}")
    logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
