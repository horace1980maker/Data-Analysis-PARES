"""
Diagnostic script to check what columns exist in the input file
and why Storyline 3 metrics might be empty.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), "storyline3_pipeline"))

from storyline3.io import load_tables
from storyline3.config import DIF_GROUP_CANDIDATES, BARRIER_CANDIDATES, ACCESS_CANDIDATES, INCLUSION_CANDIDATES

# Use first Excel file found in current dir or specify path
import glob
xlsx_files = glob.glob("*.xlsx")
if xlsx_files:
    input_path = xlsx_files[0]
    print(f"Using file: {input_path}")
else:
    print("No .xlsx file found in current directory")
    print("Please place your analysis-ready Excel file here or specify path")
    sys.exit(1)

print("\n" + "="*60)
print("LOADING TABLES...")
print("="*60)

tables, warnings = load_tables(input_path)

print(f"\nLoaded {len(tables)} sheets")
print(f"Warnings: {warnings}")

# Check key sheets
key_sheets = [
    "LOOKUP_CONTEXT", "LOOKUP_GEO",
    "TIDY_4_2_1_DIFERENCIADO", "TIDY_4_2_2_DIFERENCIADO",
    "TIDY_3_5_SE_MDV",
    "TIDY_7_1_RESPONDENTS", "TIDY_7_1_RESPONSES"
]

print("\n" + "="*60)
print("SHEET AVAILABILITY:")
print("="*60)

for sheet in key_sheets:
    df = tables.get(sheet)
    if df is None or df.empty:
        print(f"  ❌ {sheet}: MISSING or EMPTY")
    else:
        print(f"  ✅ {sheet}: {len(df)} rows, columns: {list(df.columns)[:5]}...")

# Check DIF columns
print("\n" + "="*60)
print("CHECKING DIF COLUMN CANDIDATES:")
print("="*60)
print(f"Looking for: {DIF_GROUP_CANDIDATES}")

for sheet_name in ["TIDY_4_2_1_DIFERENCIADO", "TIDY_4_2_2_DIFERENCIADO"]:
    df = tables.get(sheet_name)
    if df is not None and not df.empty:
        print(f"\n{sheet_name} columns: {list(df.columns)}")
        found = [c for c in DIF_GROUP_CANDIDATES if c in df.columns]
        print(f"  Matched candidates: {found}")
        if not found:
            print(f"  ⚠️ NO MATCH! Add one of these to candidates or rename column")

# Check BARRIER columns
print("\n" + "="*60)
print("CHECKING BARRIER/ACCESS COLUMN CANDIDATES:")
print("="*60)
print(f"Barrier candidates: {BARRIER_CANDIDATES}")
print(f"Access candidates: {ACCESS_CANDIDATES}")
print(f"Inclusion candidates: {INCLUSION_CANDIDATES}")

df = tables.get("TIDY_3_5_SE_MDV")
if df is not None and not df.empty:
    print(f"\nTIDY_3_5_SE_MDV columns: {list(df.columns)}")
    bar_found = [c for c in BARRIER_CANDIDATES if c in df.columns]
    acc_found = [c for c in ACCESS_CANDIDATES if c in df.columns]
    inc_found = [c for c in INCLUSION_CANDIDATES if c in df.columns]
    print(f"  Barrier matches: {bar_found}")
    print(f"  Access matches: {acc_found}")
    print(f"  Inclusion matches: {inc_found}")

print("\n" + "="*60)
print("DIAGNOSTIC COMPLETE")
print("="*60)
