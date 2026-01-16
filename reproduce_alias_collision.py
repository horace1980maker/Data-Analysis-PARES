
import pandas as pd
import io
from pares_converter.app.converter import compile_workbook

# Create an Excel file that triggers Alias Collision
# Scenario: both "indice_area" (correct) and "imdice_area" (typo alias) exist in input
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    # 3.2 Priorización
    # Required: ["fecha","admin0","paisaje","grupo","mdv ","producto_principal",
    #            "i_seg_alim","i_area","i_des_loc","i_ambiente","i_inclusion","i_total"]
    
    # We provide "i_area" via TWO source columns
    df = pd.DataFrame({
        "fecha": ["2023"],
        "admin0": ["A"],
        "paisaje": ["P"],
        "grupo": ["G"],
        "mdv ": ["M"],
        "producto_principal": ["Prod"],
        "indice_seguridad_alimentaria": [1], # maps to i_seg_alim
        "indice_area": [1],   # Source 1 for i_area
        "imdice_area": [1],   # Source 2 for i_area (collision!)
        "indice_desarrollo_local": [1], # maps to i_des_loc
        "indice_ambiente": [1], # maps to i_ambiente
        "indice_inclusion": [1], # maps to i_inclusion
        "indice_total": [1] # maps to i_total
    })
    df.to_excel(writer, sheet_name="3.2. Priorización", index=False)
    
    # Needs other sheets? No, validate_input checks per sheet line by line but raises error at end
    # REQUIRED_COLUMNS checks *every* sheet in SHEETS.
    # So we must provide ALL required sheets to avoid missing_sheet error masking our test
    # Or, we can trick it? No, validate_input iterates REQUIRED_COLUMNS keys.
    # So we must provide empty valid dataframes for other sheets
    
    from pares_converter.app.converter import REQUIRED_COLUMNS
    for sh, cols in REQUIRED_COLUMNS.items():
        if sh == "3.2. Priorización": continue
        # Creating minimal df
        dd = {c: [] for c in cols}
        pd.DataFrame(dd).to_excel(writer, sheet_name=sh, index=False)

buffer.seek(0)

print("Attempting to compile workbook with ALIAS COLLISION...")
try:
    compile_workbook(buffer, strict=True, copy_raw=False)
    print("Success?")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Caught {type(e).__name__}: {e}")
