#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storyline 2 Configuration Module
Defines sheet names, column mappings, and output table names.
"""

from pathlib import Path
from typing import List, Optional

# =============================================================================
# PATHS
# =============================================================================

def get_config_dir() -> Path:
    """Get the config directory path."""
    return Path(__file__).parent.parent / "config"

def get_weights_yaml_path() -> Path:
    """Get the weights.yaml file path."""
    return get_config_dir() / "weights.yaml"

def get_params_yaml_path() -> Path:
    """Get the params.yaml file path."""
    return get_config_dir() / "params.yaml"


# =============================================================================
# SHEET NAMES
# =============================================================================

# Required core dimension sheets
REQUIRED_SHEETS = [
    "LOOKUP_GEO",
    "LOOKUP_CONTEXT",
]

# Core dimension sheets (warn if missing)
DIMENSION_SHEETS = [
    "LOOKUP_GEO",
    "LOOKUP_CONTEXT",
    "LOOKUP_MDV",
    "LOOKUP_SE",
    "LOOKUP_ECOSISTEMA",
]

# Storyline 2 core fact sheets
STORYLINE2_SHEETS = [
    "TIDY_3_4_ECOSISTEMAS",
    "TIDY_3_4_ECO_SE",
    "TIDY_3_4_ECO_MDV",
    "TIDY_3_5_SE_MDV",
]

# Optional sheets
OPTIONAL_SHEETS = [
    "TIDY_3_5_SE_MONTHS",
    "TIDY_4_2_2_AMENAZA_SE",
    "TIDY_4_1_AMENAZAS",
    "TIDY_3_2_PRIORIZACION",
]

# QA sheets
QA_SHEETS = [
    "QA_INPUT_SCHEMA",
    "QA_PK_DUPLICATES",
    "QA_MISSING_IDS",
    "QA_FOREIGN_KEYS",
]

# All sheets to attempt loading
ALL_SHEETS = DIMENSION_SHEETS + STORYLINE2_SHEETS + OPTIONAL_SHEETS + QA_SHEETS


# =============================================================================
# COLUMN NAME CANDIDATES (for flexible column matching)
# =============================================================================

# SE code column candidates
SE_CODE_CANDIDATES = ["cod_se", "se_code", "se", "codigo_se", "se_id"]

# Ecosystem ID column candidates
ECOSISTEMA_ID_CANDIDATES = ["ecosistema_id", "eco_id", "ecosystem_id"]

# Ecosystem name column candidates
ECOSISTEMA_NAME_CANDIDATES = ["ecosistema", "ecosistema_name", "ecosystem", "nombre_ecosistema"]

# MDV columns
MDV_ID_COL = "mdv_id"
MDV_NAME_COL = "mdv_name"

# Context/Geo columns
CONTEXT_ID_COL = "context_id"
GEO_ID_COL = "geo_id"
GRUPO_COL = "grupo"
PAISAJE_COL = "paisaje"
ADMIN0_COL = "admin0"
FECHA_COL = "fecha_iso"

# Threat columns
AMENAZA_ID_COL = "amenaza_id"
TIPO_AMENAZA_COL = "tipo_amenaza"
AMENAZA_COL = "amenaza"
SUMA_COL = "suma"

# Priority column
PRIORITY_TOTAL_COL = "i_total"

# Users/access columns
NR_USUARIOS_COL = "nr_usuarios"
ACCESSO_COL = "accesso"
BARRERAS_COL = "barreras"
INCLUSION_COL = "inclusion"

# Month columns
MES_CONTRIB_COL = "mes_contrib"
MES_FALTA_COL = "mes_falta"

# Ecosystem health columns
ES_SALUD_COL = "es_salud"
CAUSAS_DEG_COL = "causas_deg"


# =============================================================================
# IMPACT COLUMNS (for TIDY_4_2_2_AMENAZA_SE)
# =============================================================================

# Version 1 impact columns
IMPACT_COLS_V1 = [
    "i_economia",
    "i_sociedad",
    "i_salud",
    "i_educacion",
    "i_ambiental",
    "i_politico",
    "i_conflictos",
    "i_migracion",
]

# Version 2 impact columns
IMPACT_COLS_V2 = [
    "i_economia",
    "i_alimentaria",
    "i_sanitaria",
    "i_ambiental",
    "i_personal",
    "i_comunitaria",
    "i_politica",
]

# Combined candidates
IMPACT_COLS_ALL = list(set(IMPACT_COLS_V1 + IMPACT_COLS_V2))


# =============================================================================
# SPANISH MONTH MAPPING
# =============================================================================

SPANISH_MONTHS = {
    "ene": 1, "enero": 1, "jan": 1, "january": 1,
    "feb": 2, "febrero": 2, "february": 2,
    "mar": 3, "marzo": 3, "march": 3,
    "abr": 4, "abril": 4, "apr": 4, "april": 4,
    "may": 5, "mayo": 5,
    "jun": 6, "junio": 6, "june": 6,
    "jul": 7, "julio": 7, "july": 7,
    "ago": 8, "agosto": 8, "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "septiembre": 9, "september": 9,
    "oct": 10, "octubre": 10, "october": 10,
    "nov": 11, "noviembre": 11, "november": 11,
    "dic": 12, "diciembre": 12, "dec": 12, "december": 12,
}


# =============================================================================
# OUTPUT TABLE NAMES
# =============================================================================

# Dimension tables
OUT_DIM_CONTEXT_GEO = "dim_context_geo"
OUT_DIM_MDV = "dim_mdv"
OUT_DIM_SE = "dim_se"
OUT_DIM_ECOSISTEMA = "dim_ecosistema"

# Ecosystem connectivity
OUT_ECOSYSTEM_SUMMARY_OVERALL = "ecosystem_summary_overall"
OUT_ECOSYSTEM_SUMMARY_BY_GRUPO = "ecosystem_summary_by_grupo"

# Service SCI
OUT_SERVICE_SCI_COMPONENTS_OVERALL = "service_sci_components_overall"
OUT_SERVICE_SCI_COMPONENTS_BY_GRUPO = "service_sci_components_by_grupo"

# Ecosystem ELI
OUT_ECOSYSTEM_ELI_OVERALL = "ecosystem_eli_overall"
OUT_ECOSYSTEM_ELI_BY_GRUPO = "ecosystem_eli_by_grupo"

# Threat Pressure on Services
OUT_TPS_OVERALL = "tps_overall"
OUT_TPS_BY_GRUPO = "tps_by_grupo"

# Indirect Vulnerability of Livelihoods
OUT_IVL_OVERALL = "ivl_overall"
OUT_IVL_BY_GRUPO = "ivl_by_grupo"


# =============================================================================
# SE CODE MAPPINGS
# =============================================================================

SE_CODE_NAMES = {
    "P1": "Alimentos",
    "P2": "Materias primas",
    "P3": "Agua dulce",
    "P4": "Recursos medicinales",
    "R1": "Regulación de la calidad del aire y el clima locales",
    "R2": "Secuestro y almacenamiento de carbono",
    "R3": "Moderación de los desastres naturales",
    "R4": "Tratamiento de las aguas residuales",
    "R5": "Prevención de la erosión y mantenimiento de la fertilidad del suelo",
    "R6": "Polinización",
    "R7": "Control biológico",
    "A1": "Hábitats para las especies",
    "A2": "Mantenimiento de la diversidad genética",
    "C1": "Actividades recreativas y salud mental y física",
    "C2": "Turismo",
    "C3": "Apreciación estética e inspiración para la cultura, el arte y el diseño",
    "C4": "Experiencia espiritual y sentido de pertenencia",
}
