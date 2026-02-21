import sys
import os
import argparse
from pares_converter.app.dashboard_generator import generate_dashboard

def main():
    parser = argparse.ArgumentParser(description="Generate Dashboard from Excel")
    parser.add_argument("input_file", help="Path to the analysis-ready Excel file (e.g., FINAL_ADEL_analysis_ready.xlsx)")
    parser.add_argument("--output_dir", default="dashboard_output", help="Directory to save the dashboard (default: dashboard_output)")
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: File '{args.input_file}' not found.")
        return

    print(f"Generating dashboard from {args.input_file}...")
    try:
        html_path, bundle_path, qa_path = generate_dashboard(args.input_file, args.output_dir)
        print("\nSUCCESS!")
        print(f"1. HTML Dashboard: {html_path}")
        print(f"2. Data Bundle:    {bundle_path}")
        print(f"3. QA Report:      {qa_path}")
        print("\nYou can now open the HTML file in your browser.")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
