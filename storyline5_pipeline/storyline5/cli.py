"""
CLI module for Storyline 5.
Command-line interface for running the SbN portfolio pipeline.
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import yaml

from .config import QA_SHEETS
from .io import (
    check_strict_requirements,
    create_runlog,
    get_row_counts,
    get_sheet_availability,
    load_optional_storyline_outputs,
    load_tables,
    write_outputs,
)
from .metrics_local import compute_all_local_metrics
from .monitoring import build_monitoring_tables
from .plots import generate_plots
from .portfolio import build_portfolio
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
    return get_default_params()


def load_weights(weights_path: str) -> dict:
    """Load weight scenarios from YAML file."""
    if os.path.exists(weights_path):
        with open(weights_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    logger.warning(f"Weights file not found: {weights_path}, using defaults")
    return get_default_weights()


def get_default_params() -> dict:
    """Return default parameters."""
    return {
        "top_n": 10,
        "bundles_per_grupo": 5,
        "max_services_per_bundle": 3,
        "max_threats_per_bundle": 3,
        "max_ecosystems_per_bundle": 2,
        "use_optional_storyline_outputs": True,
        "bundle_mode": "mdv_centred",
        "min_bundle_evidence_rows": 1,
        "tiers": {
            "do_now_top_pct": 0.33,
            "do_next_mid_pct": 0.34,
            "do_later_low_pct": 0.33,
        },
        "conflict_gate": {
            "enabled": True,
            "max_conflict_risk_for_do_now": 0.70,
            "downgrade_steps": 1,
        },
        "monitoring": {
            "max_indicators_total": 12,
            "indicators_per_bundle": 6,
            "include_governance": True,
            "include_equity": True,
        },
        "local_weights": {
            "w_priority": 0.40,
            "w_risk": 0.40,
            "w_capacity_gap": 0.20,
        },
    }


def get_default_weights() -> dict:
    """Return default weight scenarios."""
    return {
        "balanced": {
            "w_impact_potential": 0.35,
            "w_leverage": 0.25,
            "w_equity_urgency": 0.20,
            "w_feasibility": 0.20,
        },
        "equity_first": {
            "w_impact_potential": 0.30,
            "w_leverage": 0.20,
            "w_equity_urgency": 0.35,
            "w_feasibility": 0.15,
        },
        "feasibility_first": {
            "w_impact_potential": 0.30,
            "w_leverage": 0.20,
            "w_equity_urgency": 0.15,
            "w_feasibility": 0.35,
        },
    }


def main(args: list = None):
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Storyline 5: SbN Portfolio Design + Monitoring Plan Pipeline"
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
        "--weights",
        default="config/weights.yaml",
        help="Path to weights YAML file (default: config/weights.yaml)",
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
    # Optional storyline outputs
    parser.add_argument(
        "--s1",
        default=None,
        help="Path to storyline1_outputs.xlsx (optional)",
    )
    parser.add_argument(
        "--s2",
        default=None,
        help="Path to storyline2_outputs.xlsx (optional)",
    )
    parser.add_argument(
        "--s3",
        default=None,
        help="Path to storyline3_outputs.xlsx (optional)",
    )
    parser.add_argument(
        "--s4",
        default=None,
        help="Path to storyline4_outputs.xlsx (optional)",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=None,
        help="Override number of top bundles overall",
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
    logger.info("Storyline 5 Pipeline: SbN Portfolio Design + Monitoring Plan")
    logger.info("=" * 60)
    
    # 1. Load Config
    logger.info(f"Loading config from: {parsed_args.config}")
    params = load_params(parsed_args.config)
    weight_scenarios = load_weights(parsed_args.weights)
    
    # Override with CLI arguments
    if parsed_args.top_n:
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
    for name, count in list(row_counts.items())[:10]:
        logger.debug(f"  - {name}: {count} rows")
    
    # QA Summary
    qa_summary = {}
    for sheet_name in QA_SHEETS:
        qa_df = tables.get(sheet_name, pd.DataFrame())
        if not qa_df.empty:
            qa_summary[sheet_name] = len(qa_df)
    
    # Strict validation
    if parsed_args.strict:
        requirements_met, missing = check_strict_requirements(tables)
        if not requirements_met:
            logger.error("Strict mode: Missing required data:")
            for item in missing:
                logger.error(f"  - {item}")
            sys.exit(1)
    
    # 3. Load optional storyline outputs (or compute locally)
    optional_paths = {
        "s1": parsed_args.s1,
        "s2": parsed_args.s2,
        "s3": parsed_args.s3,
        "s4": parsed_args.s4,
    }
    
    if params.get("use_optional_storyline_outputs", True):
        storyline_outputs = load_optional_storyline_outputs(optional_paths)
        if any(storyline_outputs.values()):
            logger.info("Using pre-computed storyline outputs where available")
        else:
            logger.info("No pre-computed storyline outputs provided, computing locally")
    else:
        storyline_outputs = {}
    
    # 4. Compute local metrics
    logger.info("Computing local metrics...")
    metrics = compute_all_local_metrics(tables, params)
    logger.info(f"Computed {len(metrics)} metric tables")
    
    # 5. Build portfolio
    logger.info("Building SbN portfolio...")
    portfolio_tables, bundle_counts = build_portfolio(
        tables, metrics, params, weight_scenarios
    )
    logger.info(f"Built portfolio: {bundle_counts}")
    
    # Merge metrics into portfolio tables for output
    all_tables = {**metrics, **portfolio_tables}
    
    # 6. Build monitoring plan
    logger.info("Building monitoring plan...")
    monitoring_tables = build_monitoring_tables(portfolio_tables, params)
    logger.info(f"Built {len(monitoring_tables)} monitoring tables")
    
    # 7. Generate figures
    figures = {}
    if parsed_args.include_figures:
        logger.info("Generating plots...")
        figures = generate_plots(portfolio_tables, parsed_args.outdir, params)
        logger.info(f"Generated {len(figures)} figures")
    
    # 8. Generate report
    report_html = ""
    if parsed_args.include_report:
        logger.info("Generating HTML report...")
        report_html = generate_report(
            portfolio_tables,
            monitoring_tables,
            figures,
            parsed_args.input,
            warnings,
            tables,
        )
    
    # 9. Create runlog
    end_time = datetime.now()
    runlog = create_runlog(
        input_path=parsed_args.input,
        output_dir=parsed_args.outdir,
        optional_storyline_paths=optional_paths,
        warnings=warnings,
        qa_summary=qa_summary,
        tables_generated=list(all_tables.keys()),
        figures_generated=list(figures.keys()),
        params=params,
        scoring_scenarios=list(weight_scenarios.keys()),
        sheet_availability=sheet_availability,
        row_counts=row_counts,
        bundle_counts=bundle_counts,
        start_time=start_time,
        end_time=end_time,
    )
    
    # 10. Write outputs
    logger.info(f"Writing outputs to: {parsed_args.outdir}")
    output_paths = write_outputs(
        parsed_args.outdir,
        all_tables,
        figures,
        report_html,
        runlog,
        monitoring_tables,
    )
    
    # Summary
    duration = (end_time - start_time).total_seconds()
    logger.info("=" * 60)
    logger.info("Pipeline completed successfully!")
    logger.info(f"Duration: {duration:.2f} seconds")
    logger.info(f"Bundles overall: {bundle_counts.get('overall', 0)}")
    logger.info(f"Bundles by grupo: {bundle_counts.get('by_grupo', 0)}")
    logger.info(f"Tables generated: {len(all_tables)}")
    logger.info(f"Figures generated: {len(figures)}")
    logger.info(f"Monitoring indicators: {len(monitoring_tables.get('INDICATORS', pd.DataFrame()))}")
    if warnings:
        logger.warning(f"Warnings: {len(warnings)}")
        for w in warnings[:5]:
            logger.warning(f"  - {w}")
    logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
