import pandas as pd
import json

xl = pd.ExcelFile('FINAL_TIERRA_VIVA_analysis_ready.xlsx')

schema = {}
for sheet in xl.sheet_names:
    df = pd.read_excel(xl, sheet)
    schema[sheet] = {
        "columns": df.columns.tolist(),
        "rows": len(df)
    }

with open('schema_output.json', 'w', encoding='utf-8') as f:
    json.dump(schema, f, indent=2, ensure_ascii=False)

print("Schema written to schema_output.json")
