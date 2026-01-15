# PARES Tools: Excel Converter & Analyzer

A production-grade suite for processing PARES SES data:

- **Converter**: Transform raw TIERRAVIVA Excel workbooks into analysis-ready format
- **Analyzer**: Run Storyline analysis pipelines on analysis-ready workbooks

## Architecture

**Single FastAPI application** serving:
- REST API endpoints (`/convert`, `/analyze/storyline1`)
- Premium web UI with custom HTML/CSS/JS

```
http://localhost:8000/        → Main UI (Converter + Analyzer tabs)
http://localhost:8000/docs    → API documentation (Swagger)
```

---

## Quickstart

### 1) Create environment & install
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2) Run the application
```bash
uvicorn pares_converter.app.main:app --reload --port 8000
```

### 3) Open in browser
Navigate to: **http://localhost:8000/**

---

## Features

### Converter Tab
- Upload raw TIERRAVIVA Excel workbooks
- Automatic conversion to analysis-ready format
- Generates LOOKUP, TIDY, RAW, and QA tables
- Download converted workbook

### Analyzer Tab
- **Storyline 1**: "Where to Act First?" - Priority analysis with:
  - Action Priority Index (API) rankings
  - Threat severity analysis
  - Capacity gap assessment
  - Quadrant visualizations
  - HTML diagnostic reports

---

## API Endpoints

### POST `/convert`
Convert a raw Excel workbook to analysis-ready format.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file` | File | required | Excel workbook (.xlsx) |
| `org_slug` | string | "tierraviva" | Organization identifier |
| `strict` | bool | false | Fail on missing columns |
| `copy_raw` | bool | true | Include RAW sheets in output |

### POST `/analyze/storyline1`
Run Storyline 1 analysis on an analysis-ready workbook.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file` | File | required | Analysis-ready workbook (.xlsx) |
| `top_n` | int | 10 | Number of top items in rankings |
| `include_figures` | bool | true | Generate PNG visualizations |
| `include_report` | bool | true | Generate HTML report |

Returns JSON with base64-encoded outputs (Excel, HTML report, ZIP).

---

## CLI Usage

### Local conversion (no server)
```bash
python scripts/convert_local.py \
  --input /path/to/database_general_TIERRAVIVA.xlsx \
  --output /path/to/FINAL_TIERRAVIVA_analysis_ready.xlsx \
  --org-slug tierraviva
```

### Storyline 1 CLI
```bash
cd storyline1_pipeline
python -m storyline1.cli \
  --input ../FINAL_analysis_ready.xlsx \
  --outdir ./output
```

---

## Project Structure

```
pares_converter/
├── app/
│   ├── main.py           # FastAPI endpoints
│   └── converter.py      # V2 compilation logic
├── ui/
│   ├── index.html        # Main UI (tabs: Converter, Analyzer)
│   ├── style.css         # Premium dark theme styles
│   └── app.js            # Frontend logic
└── ...

storyline1_pipeline/
├── storyline1/
│   ├── cli.py            # CLI entrypoint
│   ├── config.py         # Sheet names, code expansion lookups
│   ├── io.py             # Excel I/O
│   ├── transforms.py     # Data transformations
│   ├── metrics.py        # Priority, threat, capacity metrics
│   ├── plots.py          # Matplotlib visualizations
│   └── report.py         # HTML report generator
├── config/
│   └── weights.yaml      # API weight scenarios
└── README.md             # Pipeline documentation
```

---

## Notes

### Survey Processing
The converter treats **each row in `7.1. Encuesta CA` as one survey record** and produces tidy survey tables **per "Medio de vida"** value in that row.

### Code Expansion
Reports automatically expand abbreviations:
- SE codes: P1 → Alimentos, R1 → Regulación del clima
- Threat ratings: 1-5 → Muy bajo to Muy alto  
- Conflict types: C1-C7 → Full descriptions

---

## References
See `docs/REFERENCES.md`.
