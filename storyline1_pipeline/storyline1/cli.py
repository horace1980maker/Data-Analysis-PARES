#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storyline 1 CLI Module
Command-line interface for running the Storyline 1 pipeline.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from .io import create_runlog, load_tables, write_outputs
from .metrics import compute_all_metrics
from .plots import generate_all_plots
from .report import generate_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Storyline 1: 'Where to Act First?' - Priority Analysis Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m storyline1.cli --input data/analysis_ready.xlsx --outdir output/storyline1
  python -m storyline1.cli --input data/analysis_ready.xlsx --outdir output --strict
  python -m storyline1.cli --input data/analysis_ready.xlsx --outdir output --top-n 15 --no-figures

Output Structure:
  outdir/
    tables/           - CSV files for all computed metrics
    figures/          - PNG visualizations
    report/           - storyline1.html diagnostic report
    storyline1_outputs.xlsx - Consolidated Excel workbook
    runlog.json       - Execution log with QA warnings
        """,
    )
    
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to analysis-ready Excel workbook (XLSX)",
    )
    
    parser.add_argument(
        "--outdir", "-o",
        required=True,
        help="Output directory for generated files",
    )
    
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Fail if required sheets are missing (default: continue with warnings)",
    )
    
    parser.add_argument(
        "--no-strict",
        action="store_true",
        default=False,
        help="Continue even if required sheets are missing (default behavior)",
    )
    
    parser.add_argument(
        "--include-figures",
        action="store_true",
        default=True,
        help="Generate visualization figures (default: True)",
    )
    
    parser.add_argument(
        "--no-figures",
        action="store_true",
        default=False,
        help="Skip figure generation",
    )
    
    parser.add_argument(
        "--include-report",
        action="store_true",
        default=True,
        help="Generate HTML diagnostic report (default: True)",
    )
    
    parser.add_argument(
        "--no-report",
        action="store_true",
        default=False,
        help="Skip HTML report generation",
    )
    
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Number of top items to include in rankings (default: 10)",
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (debug) logging",
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Resolve flags
    strict_mode = args.strict and not args.no_strict
    include_figures = args.include_figures and not args.no_figures
    include_report = args.include_report and not args.no_report
    
    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    if not input_path.suffix.lower() in [".xlsx", ".xls"]:
        logger.error(f"Input file must be Excel format (.xlsx): {input_path}")
        sys.exit(1)
    
    # Create output directory
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("Storyline 1: 'Where to Act First?' Pipeline")
    logger.info("=" * 60)
    logger.info(f"Input:  {input_path}")
    logger.info(f"Output: {outdir}")
    logger.info(f"Mode:   {'Strict' if strict_mode else 'Permissive'}")
    logger.info("-" * 60)
    
    start_time = datetime.now()
    
    try:
        # Step 1: Load tables
        logger.info("Step 1/5: Loading tables from workbook...")
        tables, warnings = load_tables(str(input_path))
        
        if strict_mode and warnings:
            logger.error("Strict mode: Missing required sheets. Aborting.")
            for w in warnings:
                logger.error(f"  - {w}")
            sys.exit(1)
        
        for w in warnings:
            logger.warning(w)
        
        logger.info(f"  Loaded {sum(1 for df in tables.values() if not df.empty)} tables")
        
        # Step 2: Compute metrics
        logger.info("Step 2/5: Computing metrics...")
        metrics_tables = compute_all_metrics(
            tables,
            top_n=args.top_n,
            top_n_drivers=5,
        )
        logger.info(f"  Generated {len(metrics_tables)} output tables")
        
        # Step 3: Generate figures
        figures = {}
        if include_figures:
            logger.info("Step 3/5: Generating figures...")
            figures = generate_all_plots(metrics_tables, str(outdir))
            logger.info(f"  Generated {len(figures)} figures")
        else:
            logger.info("Step 3/5: Skipping figure generation")
        
        # Step 4: Generate report
        report_html = None
        if include_report:
            logger.info("Step 4/5: Generating HTML report...")
            report_html = generate_report(
                metrics_tables,
                figures,
                str(input_path),
                warnings,
            )
            logger.info("  Report generated")
        else:
            logger.info("Step 4/5: Skipping report generation")
        
        # Step 5: Write outputs
        logger.info("Step 5/5: Writing outputs...")
        
        end_time = datetime.now()
        
        # Build QA summary
        qa_summary = {}
        for qa_name in ["QA_INPUT_SCHEMA", "QA_PK_DUPLICATES", "QA_MISSING_IDS", "QA_FOREIGN_KEYS"]:
            qa_df = tables.get(qa_name)
            if qa_df is not None and not qa_df.empty:
                qa_summary[qa_name] = len(qa_df)
            else:
                qa_summary[qa_name] = 0
        
        runlog = create_runlog(
            input_path=str(input_path),
            output_dir=str(outdir),
            warnings=warnings,
            qa_summary=qa_summary,
            tables_generated=list(metrics_tables.keys()),
            figures_generated=list(figures.keys()),
            start_time=start_time,
            end_time=end_time,
        )
        
        output_paths = write_outputs(
            str(outdir),
            metrics_tables,
            figures,
            report_html,
            runlog,
        )
        
        logger.info("-" * 60)
        logger.info("Pipeline completed successfully!")
        logger.info(f"Duration: {(end_time - start_time).total_seconds():.1f} seconds")
        logger.info(f"Tables:   {len(metrics_tables)}")
        logger.info(f"Figures:  {len(figures)}")
        logger.info(f"Report:   {'Yes' if report_html else 'No'}")
        logger.info("-" * 60)
        logger.info("Output files:")
        logger.info(f"  Excel:  {output_paths.get('xlsx', 'N/A')}")
        logger.info(f"  Report: {output_paths.get('report', 'N/A')}")
        logger.info(f"  Runlog: {output_paths.get('runlog', 'N/A')}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.exception(f"Pipeline failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
