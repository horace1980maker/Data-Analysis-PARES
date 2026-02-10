
import numpy as np
import pandas as pd
import unicodedata
import re
from typing import Any

def canonical_text(x: Any) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return ""
    s = unicodedata.normalize("NFKC", str(x))
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s.lower()

def test():
    inputs = [
        np.nan,
        float('nan'),
        None,
        "Test",
        123,
        123.45,
        np.float64(np.nan),
        np.float64(123.45)
    ]
    
    print("Testing canonical_text with generic inputs...")
    for i in inputs:
        try:
            res = canonical_text(i)
            print(f"Input: {repr(i)} -> Output: {repr(res)}")
        except Exception as e:
            print(f"Input: {repr(i)} -> ERROR: {e}")

    print("\nTesting pandas Series apply...")
    df = pd.DataFrame({"col": inputs})
    try:
        df["clean"] = df["col"].apply(canonical_text)
        print("Pandas apply success")
    except Exception as e:
        print(f"Pandas apply ERROR: {e}")

    # Test what if we have object dtype with mixed types
    print("\nTesting object dtype Series...")
    s = pd.Series(inputs, dtype=object)
    try:
        s.apply(canonical_text)
        print("Object Series apply success")
    except Exception as e:
        print(f"Object Series apply ERROR: {e}")

if __name__ == "__main__":
    test()
