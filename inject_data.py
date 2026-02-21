import re
import os

# Define paths
base_dir = r"G:\My Drive\000_CONSULTANCY\CATIE\SEGUNDA CONSULTORIA\DATABASE ANALYSIS\CONVERSION\pares_excel_converter_app - Copy"
source_file = os.path.join(base_dir, "dashboard_output.html")
target_file = os.path.join(base_dir, "test_dashboard.html")

def inject_data():
    print(f"Reading source: {source_file}")
    with open(source_file, "r", encoding="utf-8") as f:
        source_content = f.read()

    # Extract BUNDLE object
    # It starts with "const BUNDLE = {" and ends with "};"
    # We use regex to capture it.
    match = re.search(r"const BUNDLE = ({.*?});", source_content, re.DOTALL)
    if not match:
        print("Error: Could not find BUNDLE object in source file.")
        return

    bundle_data = match.group(1)
    print(f"Extracted BUNDLE data ({len(bundle_data)} chars).")

    print(f"Reading target: {target_file}")
    with open(target_file, "r", encoding="utf-8") as f:
        target_content = f.read()

    # Replace placeholder
    new_content = target_content.replace("const BUNDLE = /* __BUNDLE_DATA__ */", f"const BUNDLE = {bundle_data}")

    print(f"Writing to target: {target_file}")
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("Success: Data injected.")

if __name__ == "__main__":
    inject_data()
