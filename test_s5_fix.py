
import pandas as pd
import numpy as np
from storyline5_pipeline.storyline5.transforms import pick_first_existing_col

def test_pick_first_existing_col_numeric_header():
    # DataFrame with float column names (simulating the issue)
    df = pd.DataFrame({
        2023.0: [1, 2, 3],
        "ActualName": [4, 5, 6]
    })
    
    # This should not raise AttributeError now
    try:
        col = pick_first_existing_col(df, ["SomeCandidate", "2023.0"])
        print(f"SUCCESS: Found column '{col}' without error.")
    except Exception as e:
        print(f"FAILURE: Raised {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_pick_first_existing_col_numeric_header()
