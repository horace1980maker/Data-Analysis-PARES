# Storyline 1: "Where to Act First?" Pipeline

A production-grade automation pipeline for analyzing livelihoods, threats, and adaptive capacity from PARES analysis-ready workbooks.

## Overview

Storyline 1 answers the key decision question: **Which livelihoods and zones should be prioritized for SbN/adaptation actions, and why (evidence)?**

The pipeline generates:
1. **Clean aggregated tables** (CSV + XLSX) for overall and by-grupo analysis
2. **Standard visuals** (PNG) - bar charts, quadrant plots
3. **HTML diagnostic report** - self-contained with embedded tables and images
4. **JSON run log** with QA warnings

## Installation

```bash
cd storyline1_pipeline
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python -m storyline1.cli --input <xlsx_path> --outdir <output_dir>
```

### Examples

```bash
# Standard run with all outputs
python -m storyline1.cli --input ../test_output.xlsx --outdir ./output

# Strict mode (fail if sheets missing)
python -m storyline1.cli --input ../test_output.xlsx --outdir ./output --strict

# Skip figures (faster)
python -m storyline1.cli --input ../test_output.xlsx --outdir ./output --no-figures

# Custom top-n and verbose logging
python -m storyline1.cli --input ../test_output.xlsx --outdir ./output --top-n 15 -v
```

### CLI Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--input, -i` | Path to analysis-ready Excel workbook (required) | - |
| `--outdir, -o` | Output directory (required) | - |
| `--strict` | Fail if required sheets are missing | False |
| `--no-figures` | Skip figure generation | False |
| `--no-report` | Skip HTML report generation | False |
| `--top-n` | Number of top items in rankings | 10 |
| `--verbose, -v` | Enable debug logging | False |

## Output Structure

```
outdir/
├── tables/                          # CSV files
│   ├── priority_by_mdv_overall.csv
│   ├── priority_by_mdv_group.csv
│   ├── threats_overall.csv
│   ├── threats_by_group.csv
│   ├── risk_by_mdv_overall.csv
│   ├── capacity_overall_by_mdv.csv
│   ├── rankings_overall_balanced.csv
│   └── ... (more tables)
├── figures/                         # PNG visualizations
│   ├── bar_top_livelihoods_api_overall_balanced.png
│   ├── quadrant_priority_vs_risk_overall.png
│   ├── bar_top_threats_overall.png
│   └── ... (more figures)
├── report/
│   └── storyline1.html              # Self-contained HTML report
├── storyline1_outputs.xlsx          # All tables in one workbook
└── runlog.json                      # Execution metadata & warnings
```

## How It Works

### Overall vs By-Grupo Analysis

Every metric is computed twice:
- **Overall**: Aggregated across all geographic zones
- **By Grupo**: Aggregated within each `grupo` (e.g., Zona Alta, Zona Media, Zona Baja)

The pipeline joins context-based tables to `LOOKUP_CONTEXT` → `LOOKUP_GEO` to retrieve geographic attributes.

### Action Priority Index (API)

The API is a composite index combining:
- **Priority Score** (from TIDY_3_2_PRIORIZACION)
- **Risk Score** (from TIDY_4_2_1_AMENAZA_MDV × threat severity)
- **Capacity Gap** (1 - adaptive capacity from surveys)

Three weight scenarios are computed:
- **balanced**: 40% priority + 40% risk + 20% capacity gap
- **livelihood_first**: 50% priority + 30% risk + 20% capacity gap
- **risk_first**: 30% priority + 50% risk + 20% capacity gap

Configure weights in `config/weights.yaml`.

### Survey Response Parsing

Response ranges like "0-20", "20-40", etc. are converted to midpoints:
- "0-20" → 10
- "20-40" → 30
- "40-60" → 50
- etc.

These are then normalized to 0-1 scale.

## Required Input Sheets

The pipeline expects these sheets in the input workbook:

| Sheet | Description |
|-------|-------------|
| `LOOKUP_GEO` | Geographic dimension (geo_id, admin0, paisaje, grupo) |
| `LOOKUP_CONTEXT` | Context dimension (context_id, geo_id, fecha_iso) |
| `LOOKUP_MDV` | Livelihood dimension (mdv_id, mdv_name) |
| `TIDY_3_2_PRIORIZACION` | Livelihood priority scores |
| `TIDY_4_1_AMENAZAS` | Threat observations with severity |
| `TIDY_4_2_1_AMENAZA_MDV` | Threat impacts on livelihoods |
| `TIDY_7_1_RESPONDENTS` | Survey respondent info |
| `TIDY_7_1_RESPONSES` | Survey responses |
| `LOOKUP_CA_QUESTIONS` | Survey question metadata |

Optional QA sheets (for diagnostics):
- `QA_INPUT_SCHEMA`
- `QA_PK_DUPLICATES`
- `QA_MISSING_IDS`
- `QA_FOREIGN_KEYS`

## Code Expansion

The report automatically expands abbreviations and codes:

### Ecosystem Services (SE)
- P1 → Alimentos (Provisión)
- P2 → Materias primas
- R1 → Regulación de la calidad del aire
- etc.

### Threat Magnitude
- 1 → Muy bajo
- 2 → Bajo
- 3 → Moderado
- 4 → Alto
- 5 → Muy alto

### Conflict Types
- C1 → Competencia por recursos naturales
- C2 → Desigualdad intergeneracional o de género
- etc.

## Documentation Links

- **pandas**: https://pandas.pydata.org/docs/
- **openpyxl**: https://openpyxl.readthedocs.io/
- **matplotlib**: https://matplotlib.org/stable/
- **PyYAML**: https://pyyaml.org/wiki/PyYAMLDocumentation

## Pipeline Architecture

```
storyline1/
├── __init__.py
├── config.py      # Sheet names, columns, code lookups
├── io.py          # Excel I/O, output writing
├── transforms.py  # Data transformations (joins, scaling, parsing)
├── metrics.py     # Priority, threat, risk, capacity, API metrics
├── plots.py       # Matplotlib visualizations
├── report.py      # HTML report generation
└── cli.py         # Command-line interface
```

## License

Internal use only - PARES/CATIE methodology.
