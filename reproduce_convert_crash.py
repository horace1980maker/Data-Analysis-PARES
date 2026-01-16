
import pandas as pd
import io
from pares_converter.app.converter import compile_workbook

# Create an empty Excel file (valid format but no data)
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    pd.DataFrame().to_excel(writer, sheet_name="Sheet1")
buffer.seek(0)

print("Attempting to compile empty workbook...")
try:
    # strict=True is the default in the app for /convert if not specified otherwise
    # main.py defaults strict=False but let's check both
    compile_workbook(buffer, strict=True, copy_raw=False)
    print("Success (Strict=True)")
except ValueError as e:
    print(f"Caught expected ValueError: {e}")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Caught UNEXPECTED {type(e).__name__}: {e}")

buffer.seek(0)
print("\nAttempting to compile empty workbook (Strict=False)...")
try:
    compile_workbook(buffer, strict=False, copy_raw=False)
    print("Success (Strict=False)")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Caught UNEXPECTED {type(e).__name__}: {e}")
