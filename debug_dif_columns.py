"""
Debug script to see exactly what columns exist in TIDY_4_2_1_DIFERENCIADO
"""
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), "storyline3_pipeline"))

import pandas as pd
import glob

# Find xlsx files
xlsx_files = [f for f in glob.glob("*.xlsx") if "FINAL" in f or "analysis" in f.lower() or "ready" in f.lower()]
if not xlsx_files:
    xlsx_files = glob.glob("*.xlsx")
    
if not xlsx_files:
    print("No .xlsx files found")
    sys.exit(1)

input_path = xlsx_files[0]
print(f"Using file: {input_path}")
print()

xl = pd.ExcelFile(input_path, engine="openpyxl")
print(f"All sheets: {xl.sheet_names}")
print()

# Check TIDY_4_2_1_DIFERENCIADO
target_sheets = ["TIDY_4_2_1_DIFERENCIADO", "TIDY_4_2_2_DIFERENCIADO"]

for sheet in target_sheets:
    if sheet in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet)
        print(f"\n=== {sheet} ===")
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print(f"First 3 rows:")
        print(df.head(3))
        
        # Check for dif_group candidates
        from storyline3.config import DIF_GROUP_CANDIDATES
        print(f"\nLooking for DIF_GROUP_CANDIDATES: {DIF_GROUP_CANDIDATES}")
        found = [c for c in DIF_GROUP_CANDIDATES if c in df.columns]
        print(f"Found: {found}")
        
        # Also check lowercase
        lower_cols = [c.lower() for c in df.columns]
        lower_found = [c for c in DIF_GROUP_CANDIDATES if c.lower() in lower_cols]
        print(f"Found (case-insensitive): {lower_found}")
    else:
        print(f"\n=== {sheet} === NOT FOUND")
