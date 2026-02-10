
import pandas as pd
import os

file_path = r"G:\My Drive\000_CONSULTANCY\CATIE\SEGUNDA CONSULTORIA\DATABASE ANALYSIS\CONVERSION\pares_excel_converter_app - Copy\docs\database_general_ADEL_OBS.MODIF.xlsx"

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

try:
    xls = pd.ExcelFile(file_path, engine='openpyxl')
    print("Sheets found:", xls.sheet_names)
    print("-" * 30)

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet, nrows=0)
        print(f"Sheet: '{sheet}'")
        print(f"Columns: {list(df.columns)}")
        print("-" * 30)

except Exception as e:
    print(f"Error reading file: {e}")
