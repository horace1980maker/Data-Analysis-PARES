from __future__ import annotations

import argparse
from pares_converter.app.converter import convert_workbook

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--template", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--org-slug", default="tierraviva")
    args = p.parse_args()

    stats = convert_workbook(
        input_path=args.input,
        template_path=args.template,
        output_path=args.output,
        org_slug=args.org_slug,
    )
    print("DONE:", stats)

if __name__ == "__main__":
    main()
