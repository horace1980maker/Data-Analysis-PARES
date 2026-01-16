
import pandas as pd
import io
from pares_converter.app.converter import compile_workbook

# Create an Excel file with duplicate columns in a required sheet
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    # 3.1 is a required sheet. Required cols: ["fecha","admin0",...]
    # Let's create duplicates of "nombre"
    df = pd.DataFrame({
        "fecha": ["2023-01-01"],
        "admin0": ["A"],
        "paisaje": ["P"],
        "grupo": ["G"],
        "elemento_SES": ["Medio de vida"],
        "nombre": ["First"], # This will become "nombre"
        "nombre.1": ["Second"], # This simulates a duplicate
        "uso_fin_mdv": ["Uso"]
    })
    # Force duplicate columns by renaming
    df.columns = ["fecha","admin0","paisaje","grupo","elemento_SES","nombre","nombre","uso_fin_mdv"]
    df.to_excel(writer, sheet_name="3.1. Lluvia MdV&SE", index=False)
    
buffer.seek(0)

print("Attempting to compile workbook with duplicate columns...")
try:
    compile_workbook(buffer, strict=True, copy_raw=False)
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Caught {type(e).__name__}: {e}")
