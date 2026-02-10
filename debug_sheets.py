
import pandas as pd
import os

file_path = r"docs/database_general_CDFG_OBS.MDFxlsx.xlsx"

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

try:
    xls = pd.ExcelFile(file_path, engine="openpyxl")
    print("Sheets found:")
    for sheet in xls.sheet_names:
        print(f"'{sheet}' (len={len(sheet)})")
except Exception as e:
    print(f"Error reading file: {e}")
