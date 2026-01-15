# Storyline 2: Ecosystem-Service Lifelines

A production-grade analysis pipeline that identifies **critical ecosystem services**, **leverage ecosystems**, **threat pressures**, and **indirect livelihood vulnerability** from PARES SES data.

## What Storyline 2 Answers

1. **Which ecosystem services are most critical to livelihoods?**
   - Service Criticality Index (SCI) based on linkages, users, priority, and seasonality

2. **Which ecosystems have the most leverage (strategic value)?**
   - Ecosystem Leverage Index (ELI) combining connectivity and linked service criticality

3. **What threats are pressuring critical services?**
   - Threat Pressure on Services (TPS) weighted by threat severity

4. **Which livelihoods are indirectly vulnerable via services?**
   - Indirect Vulnerability of Livelihoods (IVL): threats → services → livelihoods

---

## Quick Start

### Installation

```bash
cd storyline2_pipeline
pip install -r requirements.txt
```

### Basic Usage

```bash
python -m storyline2.cli \
  --input ZA_TIERRA_VIVA_ANALYSIS_READY.xlsx \
  --outdir out_storyline2
```

### With Figures and Report

```bash
python -m storyline2.cli \
  --input ZA_TIERRA_VIVA_ANALYSIS_READY.xlsx \
  --outdir out_storyline2 \
  --include-figures \
  --include-report \
  --top-n 10
```

### Strict Mode (fail on missing required sheets)

```bash
python -m storyline2.cli \
  --input data.xlsx \
  --outdir output \
  --strict
```

---

## Output Structure

```
out_storyline2/
├── tables/
│   ├── dim_context_geo.csv
│   ├── ecosystem_summary_overall.csv
│   ├── ecosystem_summary_by_grupo.csv
│   ├── service_sci_components_overall.csv
│   ├── service_ranking_overall_balanced.csv
│   ├── ecosystem_eli_overall.csv
│   ├── tps_overall.csv
│   ├── ivl_overall.csv
│   └── ...
├── figures/
│   ├── bar_top_services_SCI_balanced.png
│   ├── bar_top_ecosystems_ELI_overall.png
│   ├── bar_top_threat_pressure_overall.png
│   ├── bar_top_livelihood_exposure_overall.png
│   ├── heatmap_ecosystem_vs_service_overall.png
│   ├── heatmap_service_vs_livelihood_overall.png
│   └── ...
├── report/
│   └── storyline2.html
├── storyline2_outputs.xlsx
└── runlog.json
```

---

## Key Metrics

### Service Criticality Index (SCI)

Measures how critical each ecosystem service is to livelihoods:

```
SCI = w_links_mdv * links_norm 
    + w_users * users_norm 
    + w_priority * priority_norm 
    + w_seasonality * seasonality_norm
```

**Scenarios** (defined in `config/weights.yaml`):
- `balanced`: Equal emphasis on all factors
- `livelihood_priority`: Higher weight on high-priority livelihoods
- `fragility_first`: Higher weight on seasonal gaps

### Ecosystem Leverage Index (ELI)

Measures ecosystem strategic value:

```
ELI = 0.6 * connectivity_norm + 0.4 * mean_SCI_of_linked_services
```

### Threat Pressure on Services (TPS)

Measures threat impact on services:

```
pressure = impact_total * severity_weight
```

Where `severity_weight` comes from `TIDY_4_1_AMENAZAS.suma`.

### Indirect Vulnerability of Livelihoods (IVL)

Traces threats through services to livelihoods:

```
threats → services (via TIDY_4_2_2_AMENAZA_SE)
         → livelihoods (via TIDY_3_5_SE_MDV)
```

---

## How "Overall vs By Grupo" Works

For any fact table with `context_id`:
1. Join to `LOOKUP_CONTEXT` to get `geo_id`
2. Join to `LOOKUP_GEO` to get `{admin0, paisaje, grupo, fecha_iso}`

Then:
- **Overall**: Aggregate across all records
- **By Grupo**: Group by `grupo` column and aggregate within each group

---

## Expected Input Sheets

### Required Core Dimensions
- `LOOKUP_GEO(geo_id, admin0, paisaje, grupo)`
- `LOOKUP_CONTEXT(context_id, geo_id, fecha_iso)`

### Storyline 2 Fact Tables
- `TIDY_3_4_ECOSISTEMAS` - Ecosystem observations
- `TIDY_3_4_ECO_SE` - Ecosystem-Service links
- `TIDY_3_4_ECO_MDV` - Ecosystem-Livelihood links
- `TIDY_3_5_SE_MDV` - Service-Livelihood dependencies

### Optional Enhancement Tables
- `TIDY_3_5_SE_MONTHS` - Seasonal availability
- `TIDY_4_2_2_AMENAZA_SE` - Threats impacting services
- `TIDY_4_1_AMENAZAS` - Threat severity scores
- `TIDY_3_2_PRIORIZACION` - Livelihood priority rankings

### QA Sheets (optional)
- `QA_INPUT_SCHEMA`
- `QA_PK_DUPLICATES`
- `QA_MISSING_IDS`
- `QA_FOREIGN_KEYS`

---

## Configuration

### `config/weights.yaml`

Defines SCI weight scenarios and ELI weights.

### `config/params.yaml`

Pipeline parameters:
- `top_n`: Number of top items in rankings
- `use_threat_severity_weight`: Whether to weight threats by severity
- `max_heatmap_items`: Maximum items per axis in heatmaps

---

## Module Structure

```
storyline2/
├── __init__.py     # Package init
├── config.py       # Sheet names, column mappings
├── io.py           # Excel loading, output writing
├── transforms.py   # Data transformations, normalization
├── metrics.py      # SCI, ELI, TPS, IVL computations
├── plots.py        # Matplotlib visualizations
├── report.py       # HTML report generation
└── cli.py          # Command-line interface
```

---

## Documentation Links

- **pandas**: https://pandas.pydata.org/docs/
- **openpyxl**: https://openpyxl.readthedocs.io/
- **matplotlib**: https://matplotlib.org/stable/
- **PyYAML**: https://pyyaml.org/wiki/PyYAMLDocumentation

---

## Troubleshooting

### Missing Sheets

If required sheets are missing:
- Default mode: Warns but continues with available data
- Strict mode (`--strict`): Fails with error

### Empty Results

If output tables are empty:
1. Check `runlog.json` for warnings
2. Verify input has expected sheet names
3. Check column names match expected patterns

### Column Name Mismatches

The pipeline handles common column name variations:
- SE codes: `cod_se`, `se_code`, `se`, `codigo_se`
- Ecosystem IDs: `ecosistema_id`, `eco_id`
- Impact columns: V1 and V2 schemas supported

---

## Example Output

After running with `--include-report`, open `report/storyline2.html` in a browser to see:

1. **Executive Summary** - Key statistics and top services
2. **Ecosystem Analysis** - Connectivity and ELI rankings
3. **Service Criticality** - SCI components and rankings
4. **Threats & Vulnerability** - TPS and IVL analysis
5. **Data Quality** - QA issues and warnings
