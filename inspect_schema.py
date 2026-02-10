"""
Inspect the Excel schema for dashboard planning
"""
import pandas as pd
import json

xl = pd.ExcelFile('FINAL_tv_ZA_analysis_ready_20260114_1026_01.xlsx')

schema = {}
for sheet in xl.sheet_names:
    df = pd.read_excel(xl, sheet)
    schema[sheet] = {
        "columns": df.columns.tolist(),
        "rows": len(df)
    }

# Output as JSON for easy parsing
with open('schema_output.json', 'w', encoding='utf-8') as f:
    json.dump(schema, f, indent=2, ensure_ascii=False)

print("Schema written to schema_output.json")
