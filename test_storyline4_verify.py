#!/usr/bin/env python3
"""Test Storyline 4 metrics."""
import sys
import traceback
sys.path.insert(0, "storyline4_pipeline")

from storyline4.io import load_tables
from storyline4.metrics import process_metrics

def main():
    print("Loading tables...")
    tables, warnings = load_tables("FINAL_tv_ZA_analysis_ready_20260114_1026_01.xlsx")
    print(f"Loaded {len(tables)} tables")
    
    print("Running process_metrics...")
    try:
        metrics = process_metrics(tables, {"top_n": 10})
        print("Success! Generated metrics:")
        for k, v in metrics.items():
            print(f" - {k}: {len(v)} rows")
    except Exception as e:
        traceback.print_exc()
        print(f"\nError: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
