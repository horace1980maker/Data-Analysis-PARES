# Storyline 5 Pipeline

## Overview

**Storyline 5: SbN Portfolio Design + Monitoring Plan**

This pipeline answers the decision questions:
> *Which SbN/adaptation action bundles should we prioritize? How do we monitor their implementation?*

The analysis produces:
- **Candidate SbN bundles**: Data-driven packages of livelihoods (MdV) + critical services + supporting ecosystems + driver threats
- **Portfolio rankings**: Multiple scoring scenarios (balanced, equity-first, feasibility-first)
- **Tier assignments**: Do now / Do next / Do later with conflict risk gating
- **MEAL-ready monitoring plan**: Indicator library with bundle-to-indicator mappings

> ⚠️ **Evidence-Only Approach**: All bundles are labeled as "candidates to be measured/validated". We do NOT claim ecological effects or what will work.

## Installation

```bash
cd storyline5_pipeline
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python -m storyline5.cli --input <path_to_xlsx> --outdir <output_directory>
```

### Full Example

```bash
python -m storyline5.cli \
    --input ../FINAL_tv_ZA_analysis_ready_20260114_1026_01.xlsx \
    --outdir output_storyline5 \
    --include-figures \
    --include-report \
    --top-n 10
```

### Using Pre-computed Storyline Outputs

```bash
python -m storyline5.cli \
    --input ../FINAL_tv_ZA_analysis_ready_20260114_1026_01.xlsx \
    --outdir output_storyline5 \
    --s1 ../storyline1_pipeline/output/storyline1_outputs.xlsx \
    --s2 ../storyline2_pipeline/output/storyline2_outputs.xlsx \
    --s3 ../storyline3_pipeline/output/storyline3_outputs.xlsx \
    --s4 ../storyline4_pipeline/output/storyline4_outputs.xlsx
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--input` | Path to analysis-ready XLSX workbook | Required |
| `--outdir` | Directory for outputs | Required |
| `--config` | Path to params YAML file | `config/params.yaml` |
| `--weights` | Path to weights YAML file | `config/weights.yaml` |
| `--strict` | Fail if required sheets are missing | `False` |
| `--include-figures` | Generate visualization figures | `True` |
| `--include-report` | Generate HTML report | `True` |
| `--s1` | Path to storyline1_outputs.xlsx | None |
| `--s2` | Path to storyline2_outputs.xlsx | None |
| `--s3` | Path to storyline3_outputs.xlsx | None |
| `--s4` | Path to storyline4_outputs.xlsx | None |
| `--top-n` | Override number of top bundles | 10 |
| `--verbose` | Enable debug logging | `False` |

## How "Overall vs By Grupo" Works

The pipeline supports both overall (entire landscape) and by-grupo (e.g., Zona Alta/Media/Baja) analysis:

1. Every fact table with `context_id` is joined to `LOOKUP_CONTEXT → LOOKUP_GEO`
2. This adds `grupo`, `paisaje`, `admin0`, `fecha_iso` to each record
3. Bundles are constructed twice:
   - **Overall**: Top N MdV across all groups
   - **By Grupo**: Top N MdV per grupo

## Expected Input Sheets

### Required
- `LOOKUP_CONTEXT` - Context dimension with geo_id, fecha_iso
- `LOOKUP_GEO` - Geographic dimension with admin0, paisaje, grupo
- `LOOKUP_MDV` - Livelihoods dimension

### Storyline 1 Sources (Impact Potential)
- `TIDY_3_2_PRIORIZACION` - Priority ranking
- `TIDY_4_1_AMENAZAS` - Threat catalog
- `TIDY_4_2_1_AMENAZA_MDV` - Threat-livelihood linkages
- `TIDY_7_1_RESPONSES` - Survey responses (capacity)

### Storyline 2 Sources (Leverage)
- `TIDY_3_5_SE_MDV` - Service-livelihood linkages
- `TIDY_3_4_ECO_SE` - Ecosystem-service linkages
- `TIDY_3_4_ECOSISTEMAS` - Ecosystems

### Storyline 3 Sources (Equity)
- `TIDY_4_2_1_DIFERENCIADO` - Differentiated impacts

### Storyline 4 Sources (Feasibility)
- `TIDY_5_1_RELACIONES` - Actor relations
- `TIDY_5_2_DIALOGO` - Dialogue spaces
- `TIDY_6_1_CONFLICT_EVENTS` - Conflict events

## Output Structure

```
<outdir>/
├── tables/                           # CSV files for each metric
│   ├── BUNDLES_OVERALL.csv
│   ├── BUNDLE_RANKING_OVERALL_BALANCED.csv
│   ├── BUNDLE_EVIDENCE_OVERALL.csv
│   ├── COVERAGE_SUMMARY.csv
│   └── ...
├── figures/                          # PNG visualizations
│   ├── portfolio_matrix_overall_balanced.png
│   ├── stacked_components_balanced.png
│   ├── tier_distribution_balanced.png
│   └── ...
├── report/
│   └── storyline5.html               # Single-file HTML report
├── storyline5_outputs.xlsx           # Multi-sheet Excel with all outputs
├── monitoring_plan.xlsx              # MEAL-ready monitoring plan
└── runlog.json                       # Execution metadata
```

## Scoring Scenarios

Three weight scenarios are available in `config/weights.yaml`:

| Scenario | Impact | Leverage | Equity | Feasibility |
|----------|--------|----------|--------|-------------|
| `balanced` | 0.35 | 0.25 | 0.20 | 0.20 |
| `equity_first` | 0.30 | 0.20 | 0.35 | 0.15 |
| `feasibility_first` | 0.30 | 0.20 | 0.15 | 0.35 |

## Monitoring Plan

The pipeline generates a MEAL-ready monitoring plan with:

- **Indicator Library**: 10-12 indicators across OUTPUT, OUTCOME, GOVERNANCE, EQUITY, CAPACITY, RISK types
- **Bundle-Indicator Mapping**: Each bundle linked to 4-6 relevant indicators
- **Template ready for follow-up**: Indicators are phrased as "to track/measure" without claiming impact

## References

- **pandas**: https://pandas.pydata.org/docs/
- **openpyxl**: https://openpyxl.readthedocs.io/
- **matplotlib**: https://matplotlib.org/stable/
- **PyYAML**: https://pyyaml.org/wiki/PyYAMLDocumentation

---

This pipeline is part of the PARES Methodology suite for Nature-based Solutions analysis.
