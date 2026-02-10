
import pandas as pd
import numpy as np
import os

def check_file(path, label):
    print(f"\n--- Checking {label} ---")
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    try:
        xl = pd.ExcelFile(path)
        print(f"Sheets: {xl.sheet_names}")
        
        # Check specific sheets for ID columns
        target_sheets = {
            "LOOKUP_MDV": ["mdv_id"],
            "TIDY_3_2_PRIORIZACION": ["mdv_id", "priorizacion_id"],
            "TIDY_4_1_AMENAZAS": ["amenaza_id"],
            "TIDY_4_2_1_AMENAZA_MDV": ["mdv_id", "amenaza_id"]
        }
        
        for sheet, cols in target_sheets.items():
            if sheet in xl.sheet_names:
                df = pd.read_excel(xl, sheet_name=sheet)
                print(f"\nSheet: {sheet}")
                for col in cols:
                    if col in df.columns:
                        dtype = df[col].dtype
                        sample = df[col].dropna().head(3).tolist()
                        has_nans = df[col].isna().any()
                        print(f"  Column '{col}': dtype={dtype}, has_nans={has_nans}, sample={sample}")
                        
                        # Check for mixed types explicitly
                        types = df[col].apply(type).value_counts()
                        print(f"  Type distribution: {types.to_dict()}")
                    else:
                        print(f"  Column '{col}' NOT FOUND")
            else:
                print(f"Sheet '{sheet}' NOT FOUND")
                
    except Exception as e:
        print(f"Error reading file: {e}")

file1 = r"G:\My Drive\000_CONSULTANCY\CATIE\SEGUNDA CONSULTORIA\DATABASE ANALYSIS\CONVERSION\pares_excel_converter_app - Copy\FINAL_ASOVERDE_analysis_ready1.xlsx"
file2 = r"G:\My Drive\000_CONSULTANCY\CATIE\SEGUNDA CONSULTORIA\DATABASE ANALYSIS\CONVERSION\pares_excel_converter_app - Copy\FINAL_ASOVERDE_analysis_ready2.xlsx"

check_file(file1, "FILE 1 (OLD - WORKS)")
check_file(file2, "FILE 2 (NEW - FAILS)")
