#!/usr/bin/env python3
"""Diagnose ECO_SM file structure - detailed check."""

import pandas as pd

with open('diagnose_output.txt', 'w', encoding='utf-8') as f:
    f.write("=== ECO_SM vs OK FILE DIAGNOSIS ===\n\n")
    
    xl_eco = pd.ExcelFile(r'dabatase_general_ECO_SM.xlsx', engine='openpyxl')
    xl_ok = pd.ExcelFile(r'OK.xlsx', engine='openpyxl')
    
    # Check several sheets
    for sh in ['3.1. Lluvia MdV&SE', '3.2. Priorización', '4.1. Amenazas']:
        f.write(f"\n=== {sh} ===\n")
        
        # ECO_SM
        if sh in xl_eco.sheet_names:
            df = pd.read_excel(xl_eco, sh, dtype=object, nrows=0)
            f.write(f"ECO_SM columns: {list(df.columns)[:8]}\n")
        else:
            # Check with trailing space
            for eco_sh in xl_eco.sheet_names:
                if eco_sh.strip() == sh.strip():
                    df = pd.read_excel(xl_eco, eco_sh, dtype=object, nrows=0)
                    f.write(f"ECO_SM (as '{eco_sh}'): {list(df.columns)[:8]}\n")
                    break
        
        # OK
        if sh in xl_ok.sheet_names:
            df = pd.read_excel(xl_ok, sh, dtype=object, nrows=0)
            f.write(f"OK columns: {list(df.columns)[:8]}\n")
        else:
            for ok_sh in xl_ok.sheet_names:
                if ok_sh.strip() == sh.strip():
                    df = pd.read_excel(xl_ok, ok_sh, dtype=object, nrows=0)
                    f.write(f"OK (as '{ok_sh}'): {list(df.columns)[:8]}\n")
                    break

print("Output written to diagnose_output.txt")
