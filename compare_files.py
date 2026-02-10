#!/usr/bin/env python3
"""Compare OK.xlsx and FAILED.xlsx to find differences that cause conversion failure."""

import pandas as pd
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from pares_converter.app.converter import REQUIRED_COLUMNS, SHEETS, compile_workbook

def compare_files(ok_path: str, failed_path: str):
    print("="*80)
    print("COMPARING OK.xlsx vs FAILED.xlsx")
    print("="*80)
    
    # Load both files
    ok_xl = pd.ExcelFile(ok_path, engine="openpyxl")
    failed_xl = pd.ExcelFile(failed_path, engine="openpyxl")
    
    ok_sheets = set(ok_xl.sheet_names)
    failed_sheets = set(failed_xl.sheet_names)
    
    print("\n## SHEET COMPARISON ##")
    print(f"OK sheets count: {len(ok_sheets)}")
    print(f"FAILED sheets count: {len(failed_sheets)}")
    
    only_in_ok = ok_sheets - failed_sheets
    only_in_failed = failed_sheets - ok_sheets
    
    if only_in_ok:
        print(f"\nSheets ONLY in OK: {only_in_ok}")
    if only_in_failed:
        print(f"\nSheets ONLY in FAILED: {only_in_failed}")
    
    common_sheets = ok_sheets & failed_sheets
    print(f"\nCommon sheets: {len(common_sheets)}")
    
    # Compare required sheets
    print("\n## REQUIRED SHEETS CHECK ##")
    for sheet in SHEETS:
        ok_has = sheet in ok_sheets
        failed_has = sheet in failed_sheets
        status = "OK" if ok_has and failed_has else ("MISSING IN FAILED" if ok_has and not failed_has else ("MISSING IN OK" if not ok_has and failed_has else "MISSING IN BOTH"))
        if status != "OK":
            print(f"  {sheet}: {status}")
    
    # Compare columns in required sheets
    print("\n## COLUMN COMPARISON FOR REQUIRED SHEETS ##")
    for sheet, req_cols in REQUIRED_COLUMNS.items():
        if sheet in common_sheets:
            ok_df = pd.read_excel(ok_xl, sheet, dtype=object, nrows=0)
            failed_df = pd.read_excel(failed_xl, sheet, dtype=object, nrows=0)
            
            ok_cols = set(ok_df.columns)
            failed_cols = set(failed_df.columns)
            
            only_in_ok_cols = ok_cols - failed_cols
            only_in_failed_cols = failed_cols - ok_cols
            
            # Check required columns
            ok_missing_req = [c for c in req_cols if c not in ok_cols]
            failed_missing_req = [c for c in req_cols if c not in failed_cols]
            
            if only_in_ok_cols or only_in_failed_cols or ok_missing_req or failed_missing_req:
                print(f"\n  {sheet}:")
                if ok_missing_req:
                    print(f"    OK missing required: {ok_missing_req}")
                if failed_missing_req:
                    print(f"    FAILED missing required: {failed_missing_req}")
                if only_in_ok_cols:
                    print(f"    Columns only in OK: {only_in_ok_cols}")
                if only_in_failed_cols:
                    print(f"    Columns only in FAILED: {only_in_failed_cols}")
    
    # Try to compile both and catch errors
    print("\n## COMPILATION TEST ##")
    
    print("\nTrying to compile OK.xlsx...")
    try:
        tables_ok = compile_workbook(ok_path, strict=False, copy_raw=False)
        print(f"  SUCCESS! Generated {len(tables_ok)} tables")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")
    
    print("\nTrying to compile FAILED.xlsx...")
    try:
        tables_failed = compile_workbook(failed_path, strict=False, copy_raw=False)
        print(f"  SUCCESS! Generated {len(tables_failed)} tables")
    except Exception as e:
        import traceback
        print(f"  FAILED: {type(e).__name__}: {e}")
        print("\n  TRACEBACK:")
        traceback.print_exc()

if __name__ == "__main__":
    base = r"G:\My Drive\000_CONSULTANCY\CATIE\SEGUNDA CONSULTORIA\DATABASE ANALYSIS\CONVERSION\pares_excel_converter_app - Copy"
    ok_path = os.path.join(base, "OK.xlsx")
    failed_path = os.path.join(base, "FAILED.xlsx")
    
    compare_files(ok_path, failed_path)
