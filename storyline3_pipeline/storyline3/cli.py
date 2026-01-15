import argparse
import os
import yaml
import logging
import time
from datetime import datetime
from .io import load_tables, write_outputs
from .metrics import process_metrics
from .plots import generate_plots
from .report import generate_report

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Storyline 3: Equity & Differentiated Vulnerability Pipeline")
    parser.add_argument("--input", required=True, help="Path to analysis-ready XLSX")
    parser.add_argument("--outdir", required=True, help="Directory for outputs")
    parser.add_argument("--config", default="config/params.yaml", help="Path to params YAML")
    parser.add_argument("--strict", action="store_true", help="Fail if key sheets are missing")
    parser.add_argument("--include-figures", action="store_true", default=True)
    parser.add_argument("--include-report", action="store_true", default=True)
    parser.add_argument("--top-n", type=int, default=10)
    
    args = parser.parse_args()
    start_time = time.time()
    
    # 1. Load Config
    params = {}
    if os.path.exists(args.config):
        with open(args.config, 'r') as f:
            params = yaml.safe_load(f)
    params['top_n'] = args.top_n
    
    # 2. Load Data
    logger.info(f"Loading data from {args.input}")
    tables, warnings = load_tables(args.input)
    
    # QA Summary
    qa_summary = {}
    for s in ["QA_INPUT_SCHEMA", "QA_PK_DUPLICATES", "QA_MISSING_IDS", "QA_FOREIGN_KEYS"]:
        if not tables.get(s, pd.DataFrame()).empty:
             qa_summary[s] = len(tables[s])
             
    # Strict validation
    if args.strict:
        required_present = all(not tables[s].empty for s in ["LOOKUP_CONTEXT", "LOOKUP_GEO"])
        data_present = not (tables.get("TIDY_4_2_1_DIFERENCIADO", pd.DataFrame()).empty and 
                           tables.get("TIDY_3_5_SE_MDV", pd.DataFrame()).empty)
        if not (required_present and data_present):
            logger.error("Strict mode: Missing required lookup or data sheets.")
            return

    # 3. Process Metrics
    logger.info("Computing metrics...")
    metrics = process_metrics(tables, params)
    
    # 4. Generate Visuals
    plot_map = {}
    if args.include_figures:
        logger.info("Generating plots...")
        plot_map = generate_plots(metrics, args.outdir, params)
        
    # 5. Generate Report
    report_html = ""
    if args.include_report:
        logger.info("Generating HTML report...")
        report_html = generate_report(metrics, plot_map, args.input, tables)
        
    # 6. Runlog
    runlog = {
        "timestamp": datetime.now().isoformat(),
        "input": args.input,
        "outdir": args.outdir,
        "params": params,
        "execution_time_sec": time.time() - start_time,
        "sheets_loaded": {k: len(v) for k, v in tables.items() if not v.empty},
        "metrics_computed": list(metrics.keys()),
        "qa_summary": qa_summary
    }
    
    # 7. Write Outputs
    logger.info(f"Writing outputs to {args.outdir}")
    write_outputs(args.outdir, metrics, plot_map, report_html, runlog)
    
    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    import pandas as pd # Ensure pandas is available for main block if needed
    main()
