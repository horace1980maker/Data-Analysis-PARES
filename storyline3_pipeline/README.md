# Storyline 3: Equity & Differentiated Vulnerability

This pipeline automates the analysis of equity, differentiated impacts, and service access barriers for the PARES project.

## Key Features
- **Deterministic Pipeline**: Modular Python architecture ensures repeatable results.
- **Equity Vulnerability Index (EVI)**: Computes a multi-dimensional index based on impacts, barriers, and capacity.
- **Differentiated Analysis**: Automatically aggregates data by "Overall" and "By Grupo" (Zona Alta/Media/Baja).
- **Service Barriers**: Identifies systemic exclusion and access hurdles for ecosystem services.
- **Self-Contained Report**: Produces a single HTML diagnostic report with embedded base64 visualizations.

## Tech Stack
- **Python 3.10+**
- **Pandas**: Data manipulation and aggregation ([docs](https://pandas.pydata.org/docs/))
- **Matplotlib**: Static visualizations ([docs](https://matplotlib.org/stable/))
- **Openpyxl**: Excel reading/writing ([docs](https://openpyxl.readthedocs.io/))
- **PyYAML**: Configuration management ([docs](https://pyyaml.org/wiki/PyYAMLDocumentation))

## Installation
```bash
pip install -r requirements.txt
```

## Usage
Run the pipeline via the CLI:
```bash
python -m storyline3.cli --input path/to/analysis_ready.xlsx --outdir out_storyline3 --include-figures --include-report
```

### Arguments
- `--input`: Path to the analysis-ready Excel workbook.
- `--outdir`: Directory where all tables, figures, and reports will be saved.
- `--strict`: If set, the script will fail if core sheets are missing.
- `--top-n`: Number of items to show in top-frequency charts (default: 10).

## Project Structure
- `config/`: Pipeline parameters and weights.
- `storyline3/io.py`: Handles Excel loading and output writing.
- `storyline3/transforms.py`: Logic for text normalization and data cleaning.
- `storyline3/metrics.py`: The "brain" of the pipeline; computes EVI and frequencies.
- `storyline3/plots.py`: Generates all PNG visualizations.
- `storyline3/report.py`: Assembles the final HTML diagnostic.
- `storyline3/cli.py`: Entry point for the automation.
