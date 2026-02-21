"""
Markdown -> PDF converter using Pandoc + XeLaTeX (via TinyTeX).

Produces high-quality LaTeX-typeset PDFs.

Usage:
    python scripts/md_to_pdf.py                              # Both overview files
    python scripts/md_to_pdf.py docs/RESUMEN_EJECUTIVO.md    # Single file
"""

import sys
import os
import pathlib
import pypandoc

# Path to TinyTeX binaries (adjust if needed based on installation)
TINYTEX_BIN_DIR = pathlib.Path(os.environ["APPDATA"]) / "TinyTeX" / "bin" / "windows"


def ensure_tinytex_in_path():
    """Add TinyTeX bin directory to PATH if not already present."""
    if TINYTEX_BIN_DIR.exists():
        os.environ["PATH"] += os.pathsep + str(TINYTEX_BIN_DIR)
        print(f"  [INFO] Added to PATH: {TINYTEX_BIN_DIR}")
    else:
         # Fallback check for common install location
        alt_path = pathlib.Path(os.environ["APPDATA"]) / "Roaming" / "TinyTeX" / "bin" / "windows"
        if alt_path.exists():
             os.environ["PATH"] += os.pathsep + str(alt_path)
             print(f"  [INFO] Added to PATH: {alt_path}")
        else:
            print(f"  [WARN] TinyTeX binary directory not found at expected locations.")


def convert_md_to_pdf(md_path: pathlib.Path, out_dir: pathlib.Path | None = None):
    """Convert a single .md file to a LaTeX-typeset PDF."""
    md_path = pathlib.Path(md_path).resolve()
    if not md_path.exists():
        print(f"  [X] File not found: {md_path}")
        return False

    out_dir = out_dir or md_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / md_path.with_suffix(".pdf").name

    print(f"  >> Converting {md_path.name} ...")

    # Detect language for hyphenation
    lang = "es" if "RESUMEN" in md_path.name.upper() else "en"

    # LaTeX styling arguments
    pdoc_args = [
        "--pdf-engine=xelatex",
        "-V", "geometry:margin=1in",
        "-V", f"lang={lang}",
        "-V", "fontsize=11pt",
        "-V", "mainfont=Arial", 
        "-V", "sansfont=Segoe UI",
        "-V", "monofont=Consolas",
        "-V", "linkcolor=blue",
        "-V", "urlcolor=blue",
        "--toc",      # Table of contents
        "--number-sections" # Numbered sections (1.1, 1.2)
    ]

    try:
        output = pypandoc.convert_file(
            str(md_path),
            "pdf",
            outputfile=str(pdf_path),
            extra_args=pdoc_args
        )
    except RuntimeError as e:
        print(f"  [X] Conversion failed: {e}")
        return False

    if pdf_path.exists():
        size_kb = pdf_path.stat().st_size / 1024
        print(f"  [OK] {pdf_path.name} ({size_kb:.0f} KB)")
        return True
    else:
        print(f"  [X] Output file not created.")
        return False


def main():
    ensure_tinytex_in_path()

    project = pathlib.Path(__file__).resolve().parent.parent
    docs_dir = project / "docs"

    if len(sys.argv) > 1:
        targets = [pathlib.Path(a).resolve() for a in sys.argv[1:]]
    else:
        overview_names = ["EXECUTIVE_OVERVIEW.md", "RESUMEN_EJECUTIVO.md"]
        targets = [docs_dir / n for n in overview_names if (docs_dir / n).exists()]

    if not targets:
        print("No Markdown files found.")
        return

    print(f"\n{'='*50}")
    print("  PARES -- Markdown to PDF Converter (LaTeX)")
    print(f"{'='*50}\n")

    ok = 0
    for md_file in targets:
        if convert_md_to_pdf(md_file):
            ok += 1

    print(f"\n  Done! {ok}/{len(targets)} file(s) converted.\n")


if __name__ == "__main__":
    main()
