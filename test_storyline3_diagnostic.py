import sys
import os
import pandas as pd
from datetime import datetime

# Add storyline3 to path
sys.path.insert(0, os.path.join(os.getcwd(), "storyline3_pipeline"))

try:
    from storyline3.io import load_tables, create_runlog
    from storyline3.metrics import process_metrics, load_params
    from storyline3.plots import generate_plots
    from storyline3.report import generate_report
    print("SUCCESS: Imports worked.")
except Exception as e:
    print(f"FAILED: Import error: {e}")
    sys.exit(1)

# Create dummy data
tables = {
    "LOOKUP_CONTEXT": pd.DataFrame({"context_id": ["C1"], "geo_id": ["G1"]}),
    "LOOKUP_GEO": pd.DataFrame({"geo_id": ["G1"], "geo_name": ["Test"]}),
    "TIDY_4_2_1_DIFERENCIADO": pd.DataFrame({
        "context_id": ["C1"], "mdv_id": ["M1"], "mdv_name": ["M1"], 
        "amenaza_id": ["A1"], "dif_group": ["Women"]
    }),
    "TIDY_3_5_SE_MDV": pd.DataFrame({
        "context_id": ["C1"], "mdv_id": ["M1"], "mdv_name": ["M1"],
        "barreras": ["Test"], "acceder": ["Test"], "inclusion": ["Test"],
        "grupo": ["G1"]
    })
}

try:
    print("Testing metrics...")
    params = load_params()
    params["top_n"] = 10
    metrics = process_metrics(tables, params)
    print("SUCCESS: Metrics computed.")
    
    print("Testing plots...")
    outdir = "tmp_test_plots"
    os.makedirs(outdir, exist_ok=True)
    plots = generate_plots(metrics, outdir, params)
    print(f"SUCCESS: Generated {len(plots)} plots.")
    
    print("Testing report...")
    report = generate_report(metrics, plots, "dummy_input.xlsx", tables)
    print("SUCCESS: Report generated.")
    
except Exception as e:
    import traceback
    print(f"FAILED: Runtime error: {e}")
    traceback.print_exc()
    sys.exit(1)

print("ALL TESTS PASSED.")
