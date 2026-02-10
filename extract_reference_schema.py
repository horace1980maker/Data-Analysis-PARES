import pandas as pd
import json
import os

file_path = r"g:\My Drive\000_CONSULTANCY\CATIE\SEGUNDA CONSULTORIA\DATABASE ANALYSIS\CONVERSION\pares_excel_converter_app - Copy\docs\database_general_ADEL_OBS.MODIF.xlsx"

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

try:
    xls = pd.ExcelFile(file_path, engine='openpyxl')
    schema = {}
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name, nrows=0) # Read only headers
        schema[sheet_name] = list(df.columns)
    
    print(json.dumps(schema, indent=2, ensure_ascii=False))

except Exception as e:
    print(f"Error reading excel file: {e}")
