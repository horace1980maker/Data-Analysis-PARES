# Storyline 4 Pipeline

## Overview

**Storyline 4: Feasibility, Governance & Conflict Risk**

This pipeline answers the decision question:
> *Which actions are implementable (who can do what, where), and what conflict dynamics could block implementation?*

The analysis covers:
- **Actor networks**: Who are the key actors, and how do they collaborate or conflict?
- **Dialogue spaces**: Where can action happen, and who participates?
- **Conflict dynamics**: What conflicts exist, how do they evolve, and which actors are involved?
- **Feasibility index**: A composite score combining network strength, dialogue coverage, and conflict risk.

## Installation

```bash
cd storyline4_pipeline
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python -m storyline4.cli --input <path_to_xlsx> --outdir <output_directory>
```

### Full Example

```bash
python -m storyline4.cli \
    --input ../FINAL_tv_ZA_analysis_ready_20260114_1026_01.xlsx \
    --outdir output_storyline4 \
    --include-figures \
    --include-report \
    --top-n 10
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--input` | Path to analysis-ready XLSX workbook | Required |
| `--outdir` | Directory for outputs | Required |
| `--config` | Path to params YAML file | `config/params.yaml` |
| `--strict` | Fail if required sheets are missing | `False` |
| `--include-figures` | Generate visualization figures | `True` |
| `--include-report` | Generate HTML report | `True` |
| `--top-n` | Number of top items in rankings | `10` |
| `--verbose` | Enable debug logging | `False` |

## How "Overall vs By Grupo" Works

The pipeline supports both overall (entire landscape) and by-grupo (e.g., Zona Alta/Media/Baja) analysis:

1. Every fact table with `context_id` is joined to `LOOKUP_CONTEXT → LOOKUP_GEO`
2. This adds `grupo`, `paisaje`, `admin0`, `fecha_iso` to each record
3. Metrics are computed twice:
   - **Overall**: Aggregate across all groups
   - **By Grupo**: Group by `grupo` column

## Expected Input Sheets

### Required
- `LOOKUP_CONTEXT` - Context dimension with geo_id, fecha_iso
- `LOOKUP_GEO` - Geographic dimension with admin0, paisaje, grupo

### Optional (Analysis Data)
- `TIDY_5_1_ACTORES` - Actor observations with tipo_actor, poder, interes
- `TIDY_5_1_RELACIONES` - Actor relationships (colabora/conflicto)
- `TIDY_5_2_DIALOGO` - Dialogue spaces
- `TIDY_5_2_DIALOGO_ACTOR` - Actor participation in dialogue spaces
- `TIDY_6_1_CONFLICT_EVENTS` - Conflict events with timeline
- `TIDY_6_2_CONFLICTO_ACTOR` - Actor involvement in conflicts
- `TIDY_4_2_1_MAPEO_CONFLICTO` - Threat-livelihood-conflict linkages
- `TIDY_4_2_2_MAPEO_CONFLICTO` - Threat-service-conflict linkages

### QA Sheets
- `QA_INPUT_SCHEMA`, `QA_PK_DUPLICATES`, `QA_MISSING_IDS`, `QA_FOREIGN_KEYS`

## Output Structure

```
<outdir>/
├── tables/                    # CSV files for each metric
│   ├── ACTORS_OVERALL.csv
│   ├── ACTOR_CENTRALITY_OVERALL.csv
│   ├── DIALOGUE_SPACES_OVERALL.csv
│   ├── CONFLICTS_OVERALL.csv
│   ├── FEASIBILITY_BY_GRUPO.csv
│   └── ...
├── figures/                   # PNG visualizations
│   ├── bar_top_actors_collab_overall.png
│   ├── heatmap_dyads_collab_overall.png
│   ├── line_conflict_timeline_overall.png
│   ├── bar_feasibility_by_grupo.png
│   └── ...
├── report/
│   └── storyline4.html        # Single-file HTML report (images embedded)
├── storyline4_outputs.xlsx    # Multi-sheet Excel with all metrics
└── runlog.json                # Execution metadata and QA summary
```

## Feasibility Index

The feasibility score combines three components:

```
Feasibility = w1 × Actor_Network_Strength + w2 × Dialogue_Coverage + w3 × (1 - Conflict_Risk)
```

Default weights (configurable in `params.yaml`):
- Actor Network Strength: 35%
- Dialogue Coverage: 25%
- Conflict Risk: 40%

Higher scores indicate better implementation conditions.

## References

- **pandas**: https://pandas.pydata.org/docs/
- **openpyxl**: https://openpyxl.readthedocs.io/
- **matplotlib**: https://matplotlib.org/stable/
- **PyYAML**: https://pyyaml.org/wiki/PyYAMLDocumentation

---

This pipeline is part of the PARES Methodology suite for Nature-based Solutions analysis.
