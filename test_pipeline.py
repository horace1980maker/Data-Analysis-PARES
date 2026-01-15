"""Test the updated Storyline 3 pipeline with actual data."""
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), "storyline3_pipeline"))

from storyline3.io import load_tables
from storyline3.metrics import process_metrics, load_params

import glob
xlsx_files = [f for f in glob.glob("*.xlsx") if "FINAL" in f or "analysis" in f.lower()]
if not xlsx_files:
    xlsx_files = glob.glob("*.xlsx")
input_path = xlsx_files[0]
print(f"Using file: {input_path}")

print("\n=== Loading tables ===")
tables, warnings = load_tables(input_path)
print(f"Loaded {len(tables)} sheets")
if warnings:
    print(f"Warnings: {warnings}")

print("\n=== Processing metrics ===")
params = load_params()
params["top_n"] = 10

try:
    metrics = process_metrics(tables, params)
    print(f"Generated {len(metrics)} metric tables:")
    for name, df in metrics.items():
        print(f"  - {name}: {len(df)} rows")
        if name.startswith("DIF"):
            print(f"    Columns: {list(df.columns)}")
            print(f"    First 3 rows:")
            print(df.head(3).to_string())
except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()

print("\n=== Done ===")
