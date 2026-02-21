# Workspace Comparator Report

**Workspace A:** `pares_excel_converter_app - Copy`
**Workspace B:** `pares_excel_converter_app_WIP`

## Feature Probe Results

| # | Feature | pares_excel_converter_app - Copy | pares_excel_converter_app_WIP | Winner |
|---|---------|---|---|--------|
| 1 | Robust Column Matching (7.1) | ✅ Found: country_candidates, group_candidates, mdv_candidates, size_candidates | ✅ Found: country_candidates, group_candidates, mdv_candidates, size_candidates | Tie |
| 2 | Aggregated Data Format Support | ❌ average_valor=✗, m_d_v=✗ | ✅ average_valor=✓, m_d_v=✓ | **pares_excel_converter_app_WIP** |
| 3 | tidy_7_1_ca returns 3 tables | ❌ Returns only 2 tables (respondents, responses) — NO capacity | ✅ Returns 3 tables (respondents, responses, capacity) | **pares_excel_converter_app_WIP** |
| 4 | Config includes TIDY_7_1_CAPACITY | ❌ TIDY_7_1_CAPACITY is MISSING from config — pipeline will drop it | ✅ TIDY_7_1_CAPACITY is listed in config | **pares_excel_converter_app_WIP** |
| 5 | capacity_metrics(4 args) | ❌ capacity_metrics has NO tidy_capacity parameter — cannot use aggregated data | ✅ capacity_metrics accepts tidy_capacity (4th arg) | **pares_excel_converter_app_WIP** |
| 6 | Type casts (.astype) in converter | ✅ 17 casts: str×17 | ✅ 18 casts: str×18 | Tie |
| 7 | mdv_id explicit casting | ❌ mdv_id is NOT explicitly cast — will cause MergeError on mixed types | ❌ mdv_id is NOT explicitly cast — will cause MergeError on mixed types | Neither |
| 8 | Safe .lower() usage | ❌ 13 unguarded .lower() calls (out of 15) — risk of AttributeError on floats | ❌ 13 unguarded .lower() calls (out of 15) — risk of AttributeError on floats | Neither |
| 9 | canonical_text() normalization | ✅ 62 uses of canonical_text() — good normalization | ✅ 63 uses of canonical_text() — good normalization | Tie |
| 10 | Sheet name aliasing | ✅ Sheet alias logic found | ✅ SHEET_NAME_ALIASES defined — flexible sheet name matching | Tie |

## Function-Level Differences

### pares_converter/app/converter.py
| Function | Status | Lines (A) | Lines (B) |
|----------|--------|-----------|-----------|
| `build_lookup_ca_questions` | DIFFERS | 25 | 40 |
| `get_context_id` | ONLY in A | 3 | - |
| `read_workbook` | DIFFERS | 15 | 29 |
| `tidy_3_2_priorizacion` | DIFFERS | 32 | 23 |
| `tidy_7_1_ca` | DIFFERS | 102 | 144 |

### storyline1_pipeline/storyline1/metrics.py
| Function | Status | Lines (A) | Lines (B) |
|----------|--------|-----------|-----------|
| `capacity_metrics` | DIFFERS | 122 | 171 |
| `compute_all_metrics` | DIFFERS | 80 | 90 |

## Summary

| Metric | Count |
|--------|-------|
| **pares_excel_converter_app - Copy wins** | 0 |
| **pares_excel_converter_app_WIP wins** | 4 |
| **Ties** | 6 |

> **⚠️ pares_excel_converter_app_WIP has more working features.** Consider porting fixes from B → A.